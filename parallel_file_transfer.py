import asyncio
import hashlib
import math
import os
from collections import defaultdict
from typing import AsyncGenerator, BinaryIO, Tuple, Union

from telethon import TelegramClient, helpers, utils
from telethon.crypto import AuthKey
from telethon.network import MTProtoSender
from telethon.tl.functions import InvokeWithLayerRequest
from telethon.tl.functions.auth import ExportAuthorizationRequest, ImportAuthorizationRequest
from telethon.tl.functions.upload import SaveBigFilePartRequest, SaveFilePartRequest
from telethon.tl.types import Document, InputDocumentFileLocation, InputFile, InputFileBig, InputFileLocation, InputPeerPhotoFileLocation, InputPhotoFileLocation, TypeInputFile

TypeLocation = Union[Document, InputDocumentFileLocation, InputPeerPhotoFileLocation, InputFileLocation, InputPhotoFileLocation]

class DownloadSender:
    def __init__(self, client, sender, file, offset, limit, stride, count):
        self.sender, self.client, self.request = sender, client, GetFileRequest(file, offset=offset, limit=limit)
        self.stride, self.remaining = stride, count
    async def next(self):
        if not self.remaining: return None
        result = await self.client._call(self.sender, self.request)
        self.remaining -= 1
        self.request.offset += self.stride
        return result.bytes
    def disconnect(self): return self.sender.disconnect()

class UploadSender:
    def __init__(self, client, sender, file_id, part_count, big, index, stride, loop):
        self.client, self.sender, self.part_count, self.stride, self.loop = client, sender, part_count, stride, loop
        self.request = SaveBigFilePartRequest(file_id, index, part_count, b"") if big else SaveFilePartRequest(file_id, index, b"")
        self.previous = None
    async def next(self, data):
        if self.previous: await self.previous
        self.previous = self.loop.create_task(self._next(data))
    async def _next(self, data):
        self.request.bytes = data
        await self.client._call(self.sender, self.request)
        self.request.file_part += self.stride
    async def disconnect(self):
        if self.previous: await self.previous
        return await self.sender.disconnect()

class ParallelTransferrer:
    def __init__(self, client, dc_id=None):
        self.client, self.loop, self.dc_id, self.senders, self.upload_ticker = client, client.loop, dc_id or client.session.dc_id, None, 0
        self.auth_key = None if dc_id and client.session.dc_id != dc_id else client.session.auth_key
    async def _cleanup(self): await asyncio.gather(*[sender.disconnect() for sender in self.senders])
    def _get_connection_count(self, file_size): return 20 if file_size > 100 * (1024**2) else math.ceil((file_size / (100 * (1024**2))) * 20)
    async def _create_sender(self):
        dc = await self.client._get_dc(self.dc_id)
        sender = MTProtoSender(self.auth_key, loggers=self.client._log)
        await sender.connect(self.client._connection(dc.ip_address, dc.port, dc.id, loggers=self.client._log, proxy=self.client._proxy))
        if not self.auth_key:
            auth = await self.client(ExportAuthorizationRequest(self.dc_id))
            self.client._init_request.query = ImportAuthorizationRequest(id=auth.id, bytes=auth.bytes)
            req = InvokeWithLayerRequest(LAYER, self.client._init_request)
            await sender.send(req)
            self.auth_key = sender.auth_key
        return sender
    async def init_upload(self, file_id, file_size, part_size_kb=None, connection_count=None):
        connection_count = connection_count or self._get_connection_count(file_size)
        part_size = (part_size_kb or utils.get_appropriated_part_size(file_size)) * 1024
        part_count = (file_size + part_size - 1) // part_size
        is_large = file_size > 10 * (1024**2)
        await self._init_upload(connection_count, file_id, part_count, is_large)
        return part_size, part_count, is_large
    async def upload(self, part): await self.senders[self.upload_ticker].next(part); self.upload_ticker = (self.upload_ticker + 1) % len(self.senders)
    async def finish_upload(self): await self._cleanup()
    async def download(self, file, file_size, part_size_kb=None, connection_count=None):
        connection_count = connection_count or self._get_connection_count(file_size)
        part_size = (part_size_kb or utils.get_appropriated_part_size(file_size)) * 1024
        part_count = math.ceil(file_size / part_size)
        await self._init_download(connection_count, file, part_count, part_size)
        part = 0
        while part < part_count:
            tasks = [self.loop.create_task(sender.next()) for sender in self.senders]
            for task in tasks:
                data = await task
                if not data: break
                yield data
                part += 1
        await self._cleanup()

parallel_transfer_locks = defaultdict(lambda: asyncio.Lock())

def stream_file(file_to_stream, chunk_size=1024):
    while True:
        data_read = file_to_stream.read(chunk_size)
        if not data_read: break
        yield data_read

async def _internal_transfer_to_telegram(client, response, filename, progress_callback):
    file_id, file_size = helpers.generate_random_long(), os.path.getsize(response.name)
    hash_md5, uploader = hashlib.md5(), ParallelTransferrer(client)
    part_size, part_count, is_large = await uploader.init_upload(file_id, file_size)
    buffer = bytearray()
    for data in stream_file(response):
        if progress_callback: await _maybe_await(progress_callback(response.tell(), file_size))
        if not is_large: hash_md5.update(data)
        if len(buffer) == 0 and len(data) == part_size: await uploader.upload(data); continue
        new_len = len(buffer) + len(data)
        if new_len >= part_size: cutoff = part_size - len(buffer); buffer.extend(data[:cutoff]); await uploader.upload(bytes(buffer)); buffer.clear(); buffer.extend(data[cutoff:])
        else: buffer.extend(data)
    if len(buffer) > 0: await uploader.upload(bytes(buffer))
    await uploader.finish_upload()
    return (InputFileBig(file_id, part_count, filename), file_size) if is_large else (InputFile(file_id, part_count, filename, hash_md5.hexdigest()), file_size)

async def download_file(client, location, out, progress_callback=None):
    size, dc_id, location = location.size, *utils.get_input_location(location)
    downloader, downloaded = ParallelTransferrer(client, dc_id), downloader.download(location, size)
    async for x in downloaded: out.write(x); if progress_callback: await _maybe_await(progress_callback(out.tell(), size))
    return out

async def upload_file(client, file, filename, progress_callback=None):
    return (await _internal_transfer_to_telegram(client, file, filename, progress_callback))[0]
                   
