from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import aio_pika
import asyncio
import os

app = FastAPI()

async def get_rabbitmq_connection():
    return await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    file_path = f"/app/shared_volume/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=file.filename.encode()),
            routing_key="image_queue"
        )
    
    return {"filename": file.filename, "status": "Processing"}

@app.get("/video/{filename}")
async def get_video(filename: str):
    video_path = f"/app/shared_volume/{filename.split('.')[0]}.mp4"
    if os.path.exists(video_path):
        return FileResponse(video_path)
    return {"error": "Video not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)