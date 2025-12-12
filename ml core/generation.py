from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import json
import time
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = "3A8BFC7A9DF2EF10128662A59C711A8D"
SECRET_KEY = "2CCB53EA8DE9B5E8E3B042E52603D4A1"

BASE_URL = "https://api-key.fusionbrain.ai/"
HEADERS = {
    "X-Key": f"Key {API_KEY}",
    "X-Secret": f"Secret {SECRET_KEY}",
}

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Image Generation API is running", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "image-generation-api"}


class PromptRequest(BaseModel):
    prompt: str
    width: int = 768
    height: int = 768
    num_images: int = 1


def get_pipeline_id():
    try:
        resp = requests.get(BASE_URL + "key/api/v1/pipelines", headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        if not data or len(data) == 0:
            raise Exception("No pipelines available")
        return data[0]["id"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting pipeline ID: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to get pipeline ID: {str(e)}")
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing pipeline response: {e}")
        raise HTTPException(status_code=503, detail="Invalid pipeline response format")


def start_generation(prompt, pipeline_id, width, height, num_images):
    try:
        params = {
            "type": "GENERATE",
            "numImages": num_images,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }

        files = {
            "pipeline_id": (None, pipeline_id),
            "params": (None, json.dumps(params), "application/json"),
        }

        resp = requests.post(BASE_URL + "key/api/v1/pipeline/run", headers=HEADERS, files=files)
        resp.raise_for_status()
        response_data = resp.json()
        
        if "uuid" not in response_data:
            logger.error(f"Response missing uuid: {response_data}")
            raise HTTPException(status_code=500, detail="Invalid response from generation API")
        
        return response_data["uuid"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error starting generation: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to start generation: {str(e)}")
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing generation response: {e}, Response: {resp.text if 'resp' in locals() else 'N/A'}")
        raise HTTPException(status_code=500, detail=f"Invalid generation response format: {str(e)}")


def wait_for_image(task_id, max_attempts=60):
    attempts = 0
    while attempts < max_attempts:
        try:
            resp = requests.get(BASE_URL + f"key/api/v1/pipeline/status/{task_id}", headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") == "DONE":
                if "result" not in data or "files" not in data["result"]:
                    logger.error(f"Invalid response structure: {data}")
                    raise HTTPException(status_code=500, detail="Invalid response structure from API")
                return data["result"]["files"]
            
            if data.get("status") == "FAIL":
                error_msg = data.get("error", "Generation failed")
                logger.error(f"Generation failed: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Generation failed: {error_msg}")

            attempts += 1
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking generation status: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to check generation status: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in wait_for_image: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    raise HTTPException(status_code=504, detail="Generation timeout: image generation took too long")


@app.post("/generate")
def generate_img(req: PromptRequest):
    filename = None
    try:
        logger.info(f"Starting image generation with prompt: {req.prompt}")
        
        pipeline_id = get_pipeline_id()
        logger.info(f"Got pipeline ID: {pipeline_id}")
        
        task_id = start_generation(req.prompt, pipeline_id, req.width, req.height, req.num_images)
        logger.info(f"Started generation task: {task_id}")
        
        urls = wait_for_image(task_id)
        logger.info(f"Generation complete, got {len(urls)} image(s)")

        # скачиваем картинку
        if not urls or len(urls) == 0:
            raise HTTPException(status_code=500, detail="No image URLs returned")
        
        img_url = urls[0]
        logger.info(f"Downloading image from: {img_url}")
        
        img_resp = requests.get(img_url, timeout=30)
        img_resp.raise_for_status()
        img_bytes = img_resp.content

        filename = f"result_{uuid.uuid4()}.png"
        with open(filename, "wb") as f:
            f.write(img_bytes)
        
        logger.info(f"Image saved to {filename}")
        return FileResponse(filename, media_type="image/png")
    
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to download image: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in generate_img: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Можно добавить очистку временных файлов при необходимости
        pass
