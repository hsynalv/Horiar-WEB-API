import datetime
import json
import logging
import math
import os
import openai
import random

from app.models.dataset_model import Dataset
from app.models.image_request_model import ImageRequest
from app.models.text_to_image_model import TextToImage
from app.services.base_service import BaseService
from dotenv import load_dotenv

from app.utils.notification import notify_status_update
from app.utils.queue_manager import add_to_image_queue, redis_conn
from app.utils.runpod_requets import send_runpod_request
from app.utils.convert_to_webp import process_and_save_image

load_dotenv(dotenv_path="/var/www/Horiar-WEB-API/.env.production")
openai.api_key = os.getenv("OPEN_AI_KEY")


class TextToImageService(BaseService):
    model = None
    Duty = {
        'clip_l': """
                    You are an AI assistant specialized in enhancing image generation prompts for the clip_l text encoder in Stable Diffusion XL (SDXL). When a user provides a prompt:
                    - Identify Key Elements:
                        - Read the t5xxl prompt and extract the main subject, important descriptors, styles, moods, lighting, camera details, and any artistic or brand references.
                    - Extract Essential Details:
                        - Focus on the most significant aspects that define the image.
                        - Omit filler words and less critical information.
                    - Reorganize into a Concise Format:
                        - Arrange the extracted elements into a brief, keyword-rich prompt.
                        - Use commas or semicolons to separate different descriptors.
                        - Place the main subject first, followed by descriptors and modifiers.
                    - Maintain Original Intent:
                        -Ensure the reorganized prompt preserves the original meaning and important details of the t5xxl prompt.
                    - Format for clip_l:
                        Keep the prompt concise and focused.
                        Use specific keywords effective for clip_l, such as:
                            Image quality: hyper-realistic, ultra-detailed, 8K resolution.
                            Artistic style: cinematic, digital art, photorealistic.
                            Lighting: dramatic lighting, Rembrandt lighting, soft glow.
                            Camera and lens: Arri Alexa LF, Zeiss Master Prime 50mm f/1.4.
                            Mood: epic, mysterious, moody.
                            Artistic references: inspired by Roger Deakins, art by [artist].
            """,

        't5xxl': """
                    You are an AI assistant specialized in enhancing image generation prompts for the t5xxl text encoder in Stable Diffusion XL (SDXL). When a user provides a prompt:
                    1-) Language and Clarity:
                        - If the prompt is not in English, translate it into English before proceeding.
                        - Use clear, unambiguous words that do not have multiple meanings.
                        - Avoid fancy or ambiguous words that might alter the intended meaning.
                    2-) Detail Enhancement:
                        - If a trait in the prompt is not detailed or straightforward, redescribe it by adding appearance details to enhance clarity.
                        - Refine the prompt to be descriptive and expressive, providing a detailed narrative of the scene.
                    3-) Keyword Incorporation:
                        - Identify private keywords
                            If private names are used, include visual details from that private keyword.
                        - Identify the Intended Style or Genre:
                            -Determine the specific style or genre the user wants (e.g., anime, cartoon, cyberpunk, fantasy, realism, surrealism, abstract, portrait, landscape, steampunk, noir, horror, sci-fi, romantic, historical, minimalist).
                        - Select Appropriate Keywords and Modifiers:
                            - Style-Specific Keywords:
                            - Use terms commonly associated with the identified style.
                                - Examples include:
                                    - Anime, cartoon, cyberpunk, fantasy, realism, surrealism, abstract, portrait, landscape, steampunk, noir, horror, sci-fi, romantic, historical, minimalist.
                        - Cameras and Equipments:
                            -Incorporate high-end camera models to suggest quality and style.
                                - Examples include:
                                    - Arri Alexa LF: Known for exceptional dynamic range and color science.
                                    - RED Komodo 6K: Ideal for ultra-high-definition captures with rich detail.
                                    - Sony Alpha 1: Offers 50.1MP resolution and 8K recording capability.
                                    - Canon EOS R5: High-resolution stills and advanced video capabilities.
                        - Lenses:
                            -Specify lens types to influence depth of field and perspective.
                            -Examples include:
                                - Zeiss Master Prime 50mm f/1.4: Sharp focus with cinematic bokeh.
                                - Leica Summilux-M 35mm f/1.4 ASPH: Wide-angle shots with stunning clarity.
                                - Canon RF 85mm f/1.2L: Exquisite sharpness and depth for portraits.
                        - Lighting Techniques:
                            - Use lighting styles to set the mood and enhance the visual appeal.
                            - Examples include:
                                - Three-Point Lighting: Key light, fill light, backlight for depth.
                                - Golden Hour Lighting: Soft, warm tones during sunrise or sunset.
                                - Rembrandt Lighting: Dramatic style with a distinct triangle of light.
                        - Camera Settings:
                            - Include settings to affect image sharpness and exposure.
                            - Aperture:
                                - f/1.2 to f/2.8: Shallow depth of field for subject isolation.
                                - f/8 to f/16: Greater depth of field for landscapes or wide shots.
                            - ISO:
                                - ISO 100-400: Maintain detail and reduce noise in well-lit scenes.
                                - ISO 800-1600+: For low-light situations, adding cinematic grain.
                            -Shutter Speed:
                                - 1/500s or higher: Freeze action.
                                - 1/30s or slower: Motion blur effects in dynamic scenes.
                        - Angles and Composition:
                            - Camera Angles:
                                - Dutch Angle: Tilted for dynamic tension.
                                - Over-the-Shoulder: Creates intimacy or tension.
                                - Low Angle: Subject appears powerful or dominant.
                                - Wide Shot: Captures the entire scene, establishing setting.
                            - Composition Techniques:
                                - Rule of Thirds, leading lines, framing, negative space.
                            - Adjectives and Descriptors:
                                - Enhance the prompt with vivid descriptors.
                                - Examples include:
                                    - Hyper-realistic, ultra-detailed, cinematic, vivid, dynamic.
                                    - High-contrast, richly textured, immersive, lifelike, tactile.
                                    - Atmospheric, dramatic, epic, sublime, moody, noir, vintage, surreal.
                                    - Depth of field, bokeh, soft focus.
                            - Stylistic References:
                                - Cinematographers:
                                    - Roger Deakins: Mastery of natural light and compositions (e.g., Blade Runner 2049).
                                    - Emmanuel Lubezki: Long takes and natural light (e.g., The Revenant).
                            - Directors:
                                - Christopher Nolan: Use of IMAX cameras and large-scale compositions.
                                - Denis Villeneuve: Atmospheric, slow-burn visuals.
                            - Photographers:
                                - Gregory Crewdson: Cinematic, staged photographs with dramatic lighting.
                                - Annie Leibovitz: Iconic portraits with rich colors and depth.
                            - Brands and Studios:
                                - Pixar, Marvel Comics, Studio Ghibli, Disney, Apple Design, LEGO Style.
                        - Medium and Technique:
                            - Oil painting, watercolor, digital illustration, pencil sketch, pixel art, mixed media.
                        - Texture and Material:
                            - Smooth textures, rough surfaces, metallic sheen, organic materials, glossy finish, matte surface.
                        
                    4-) Organization: 
                        - Reorganize the prompt according to the importance of each trait, prioritizing the most significant elements.
                        - Start with the main subject, followed by descriptive details, and then stylistic modifiers.
                    5-) Maintain Original Intent:
                        - Preserve the original intent and subject of the user's prompt throughout the enhancement process.
                        - Do not add new elements that significantly alter the intended meaning or content.
                    6-) Leverage t5xxl Strengths
                        - Utilize t5xxl's ability to understand and process natural language descriptions effectively.
                        - Write in complete sentences that flow naturally.
                    7-) Response Format:
                        - Provide the enhanced prompt back to the user without adding any additional explanations or information.
                        - Ensure the final prompt is clear, descriptive, and ready for use in image generation.    
            """
    }
    Duty_Translate = "You are a translator GPT, your job is to translate the {prompt} from any language to English without any changes in the context. Be straightforward and direct for the translation"

    @staticmethod
    def update_workflow_with_prompt(path, prompt, model_type, resolution, randomSeed, prompt_fix=True):
        """
        workflow.json dosyasını okur ve verilen prompt ile günceller.
        """
        with open(path, 'r') as file:
            workflow_data = json.load(file)

        # JSON verisinde gerekli değişiklikleri yap

        if prompt_fix:
            print("prompt fix True")
            newPrompts = TextToImageService.promptEnhance(prompt)
            workflow_data["input"]["workflow"]["61"]["inputs"]["clip_l"] = newPrompts[0]
            workflow_data["input"]["workflow"]["61"]["inputs"]["t5xxl"] = newPrompts[1]
        else:
            print("prompt fix False")
            translatePrompt = TextToImageService.translatePrompt(prompt)
            workflow_data["input"]["workflow"]["61"]["inputs"]["clip_l"] = translatePrompt
            workflow_data["input"]["workflow"]["61"]["inputs"]["t5xxl"] = translatePrompt

        if(randomSeed == True):
            print("seed değişti")
            workflow_data["input"]["workflow"]["112"]["inputs"]["noise_seed"] = random.randint(10 ** 14, 10 ** 15 - 1)
        else:
            print("seed değişmedi")
        if model_type:
            print(model_type)
            if model_type == "normal":
                workflow_data['input']['workflow']['106']['inputs']['steps'] = 24
            elif model_type == "ultra detailed":
                workflow_data['input']['workflow']['106']['inputs']['steps'] = 50

        if resolution:
            print(resolution)
            width = resolution.split('x')[0]
            height = resolution.split('x')[1].split(' |')[0]
            workflow_data['input']['workflow']['71']['inputs']['width'] = width
            workflow_data['input']['workflow']['71']['inputs']['height'] = height

        return workflow_data

    @staticmethod
    def save_request_to_db(user_id, username, prompt, response, seed, model_type, resolution, randomSeed, app, prompt_fix):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """
        execution_time = response.get("executionTime")
        if execution_time is not None:
            cost = float(execution_time) * 0.00031 * 1e-3
        else:
            cost = 0.0

        image_url = response.get("output", {}).get("message")
        if ".png" in image_url:
            image_url = image_url.split(".png")[0] + ".png"

        webp_url = process_and_save_image(app, image_url, user_id)

        # TextToImage kaydı
        text_to_image_record = TextToImage(
            datetime=datetime.datetime.utcnow(),
            prompt=prompt,
            seed=seed,
            model_type=model_type,
            prompt_fix = "on" if prompt_fix else "off",
            resolution=resolution,
            image_url=image_url,
            image_url_webp=webp_url,  # WebP URL'yi de kaydediyoruz
            cost=cost,
            execution_time=execution_time,
            source="web",
            user_id=user_id,
            username=username,
            consistent=randomSeed
        )
        text_to_image_record.save()

    @staticmethod
    def get_requests_by_user_id(user_id, page=1, per_page=8):
        """
        Veritabanından kullanıcı ID'sine göre istekleri sayfalama ile getirir.
        """
        # Kullanıcıya ait toplam kayıt sayısını alıyoruz
        total_requests = TextToImage.objects(user_id=user_id, consistent=False, source="web").count()

        # Toplam sayfa sayısını hesaplıyoruz
        total_pages = math.ceil(total_requests / per_page)

        # Sayfalama için skip miktarını hesaplıyoruz
        skip = (page - 1) * per_page

        # İlgili sayfaya göre istekleri alıyoruz
        requests = TextToImage.objects(user_id=user_id, consistent=False, source="web").order_by('-datetime').skip(
            skip).limit(per_page)

        # Yeni bir liste oluşturup her öğeyi özelleştiriyoruz
        custom_requests = []
        for request in requests:
            custom_request = {
                "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
                "prompt": request.prompt,
                "image": request.image_url_webp,
                "image_png": request.image_url,
                "seed": request.seed,
                "model_type": request.model_type,
                "prompt_fix": request.prompt_fix,
                "resolution": request.resolution,
            }
            custom_requests.append(custom_request)

        # Sonuçları döndürürken toplam sayfa ve toplam kayıt sayısını da ekliyoruz

        return {
            "requests": custom_requests,
            "total_requests": total_requests,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }

        #return custom_requests

    @staticmethod
    def get_requests_by_user_id_consistent(user_id, page=1, per_page=8):
        """
        Veritabanından kullanıcı ID'sine göre istekleri sayfalama ile getirir.
        """
        # Kullanıcıya ait toplam kayıt sayısını alıyoruz
        total_requests = TextToImage.objects(user_id=user_id, consistent=True, source="web").count()

        # Toplam sayfa sayısını hesaplıyoruz
        total_pages = math.ceil(total_requests / per_page)

        # Sayfalama için skip miktarını hesaplıyoruz
        skip = (page - 1) * per_page

        # İlgili sayfaya göre istekleri alıyoruz
        requests = TextToImage.objects(user_id=user_id, consistent=True, source="web").order_by('-datetime').skip(
            skip).limit(per_page)

        # Yeni bir liste oluşturup her öğeyi özelleştiriyoruz
        custom_requests = []
        for request in requests:
            custom_request = {
                "id": str(request.id),  # ObjectId'yi string formatına çeviriyoruz
                "prompt": request.prompt,
                "image": request.image_url_webp,
                "image_png": request.image_url,
                "seed": request.seed,
                "model_type": request.model_type,
                "prompt_fix": request.prompt_fix,
                "resolution": request.resolution,
            }
            custom_requests.append(custom_request)

        # Sonuçları döndürürken toplam sayfa ve toplam kayıt sayısını da ekliyoruz

        return {
            "requests": custom_requests,
            "total_requests": total_requests,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page
        }

        #return custom_requests

    @staticmethod
    def promptEnhance(text):
        prompts = []

        response = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"{TextToImageService.Duty['t5xxl']}"},
                {"role": "user", "content": text}
            ],
            temperature=0.7,  # Allows for creative enhancements
            frequency_penalty=0.0,  # Doesn't penalize word repetition
            presence_penalty=0.0  # Neutral towards new topics
        )
        prompts.append(response.choices[0].message.content)

        response = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"{TextToImageService.Duty['clip_l']}"},
                {"role": "user", "content": prompts[0]}
            ],
            temperature=0.7,  # Allows for creative enhancements
            frequency_penalty=0.0,  # Doesn't penalize word repetition
            presence_penalty=0.0  # Neutral towards new topics
        )
        prompts.append(response.choices[0].message.content)
        prompts.reverse()
        TextToImageService.save_dataset_to_db(text, prompts)
        return prompts

    @staticmethod
    def translatePrompt(text):
        response = openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": f"{TextToImageService.Duty_Translate}"},
                {"role": "user", "content": f"prompt: {text}"}
            ],
            temperature=0.7,  # Allows for creative enhancements
            frequency_penalty=0.0,  # Doesn't penalize word repetition
            presence_penalty=0.0  # Neutral towards new topics
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content

    @staticmethod
    def save_dataset_to_db(mainPrompt, promptsFromAI):
        """
        Kullanıcı isteğini veritabanına kaydeder.
        """
        TextToImageService.model = Dataset
        dataset = Dataset(
            main_prompt=mainPrompt,
            clip_l=promptsFromAI[0],
            t5xxl=promptsFromAI[1],
        )

        dataset.save()

    def generate_image_with_queue(prompt, model_type, resolution, payload, prompt_fix, consistent ,room):
        """Kuyruğa göre image generation işlemini başlatır."""
        job = add_to_image_queue(
            TextToImageService.run_image_generation,
            prompt=prompt, model_type=model_type, resolution=resolution, payload=payload, prompt_fix=prompt_fix,
            room=room, consistent=consistent  # room parametresi yalnızca **kwargs olarak geçiliyor
        )
        notify_status_update(room, 'processing', 'Your request is being processed.')
        return job

    @staticmethod
    def run_image_generation(prompt, model_type, resolution, payload, prompt_fix, consistent, room=None):
        # create_app fonksiyonunu burada import edin
        from app import create_app

        # Flask uygulamasını başlat
        app = create_app()

        with app.app_context():
            workflow_path = os.path.join(os.getcwd(), 'app/workflows/flux_promptfix.json')

            # workflow.json dosyasını güncelle
            updated_workflow = TextToImageService.update_workflow_with_prompt(
                path=workflow_path, prompt=prompt, model_type=model_type,
                resolution=resolution, randomSeed=not consistent, prompt_fix=prompt_fix
            )
            seed = updated_workflow["input"]["workflow"]["112"]["inputs"]["noise_seed"]

            user_id = payload["sub"]
            username = payload["username"]

            # RunPod isteği gönder
            result, status_code = send_runpod_request(
                app=app, user_id=user_id, username=username,
                data=json.dumps(updated_workflow), runpod_url="RUNPOD_URL",
                timeout=360
            )

            # RunPod yanıtında "status" kontrolü yap
            if result.get("status") == "IN_QUEUE" and result.get("id"):
                # Geçerli bir yanıt alındığında Redis’e kaydet
                runpod_id = result.get("id")
                redis_data = {
                    "user_id": user_id,
                    "username": username,
                    "prompt": prompt,
                    "seed": seed,
                    "model_type": model_type,
                    "resolution": resolution,
                    "room": room,
                    "status": "IN_PROGRESS",
                    "prompt_fix": prompt_fix,
                    "consistent": consistent,
                    "job_type": "image_generation"
                }
                redis_conn.setex(f"runpod_request:{runpod_id}", 3600, json.dumps(redis_data))
                notify_status_update(room, 'in_progress', 'Your request is being processed.')
            else:
                # Yanıt geçerli değilse, kullanıcıya başarısızlık bildirimi gönder
                notify_status_update(room, 'failed', 'Your image generation request could not be processed.')
                logging.error(f"Image generation request for user {user_id} failed with status: {result.get('status')}")
                return {"message": "Image generation request failed. Please try again later."}, 500

        return result





