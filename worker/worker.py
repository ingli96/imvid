import pika
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video
import os

def process_image(image_filename):
    image_path = f"/app/shared_volume/{image_filename}"
    output_path = f"/app/shared_volume/{image_filename.split('.')[0]}.mp4"

    image = load_image(image_path)
    image = image.resize((1024, 576))

    generator = torch.manual_seed(42)
    frames = pipeline(image, num_inference_steps=25, decode_chunk_size=8, generator=generator).frames[0]
    export_to_video(frames, output_path, fps=6)

# Load the model once
pipeline = StableVideoDiffusionPipeline.from_pretrained(
    "stabilityai/stable-video-diffusion-img2vid-xt-1-1",
    torch_dtype=torch.float16,
    variant="fp16",
)
pipeline.to("cuda")

# RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='image_queue')

def callback(ch, method, properties, body):
    image_filename = body.decode()
    process_image(image_filename)
    print(f" [x] Processed {image_filename}")

channel.basic_consume(queue='image_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()