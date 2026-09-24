# Understanding the AI model behind LiveGrid

**Powered by Stability AI.**

These downloads contain **SD-Turbo**, the pretrained text-to-image model that creates LiveGrid’s imagery on your computer. They are the model’s learned parameters—usually called **weights**—rather than video clips, a collection of prompts, or the LiveGrid application itself.

You only need these separate downloads if you want to prepare the model locally in advance or transfer it to a computer for offline use. Otherwise, LiveGrid downloads the required model files from Hugging Face on its first run.

## What are model weights?

During training, a neural network learns numerical values that influence how it processes inputs. Those values are saved in weight files. When you type a prompt, the application loads the weights and performs **inference**: using what the model learned to create a new image.

Typing a prompt does not retrain the model or rewrite its weights. These files are unchanged pretrained weights from Stability AI, not a model trained on your prompts, projection setup, or personal files.

## Why SD-Turbo?

SD-Turbo is a distilled version of Stable Diffusion 2.1, designed to generate an image in very few steps. LiveGrid uses a **single diffusion step at 512 × 512 pixels**. That favors responsiveness for live visual experimentation over the detail and prompt accuracy of larger, slower models.

The files use **fp16**, or half-precision floating-point numbers. This reduces weight storage and GPU memory requirements compared with full precision. They are stored in **Safetensors**, a format for numerical tensors rather than executable Python model objects.

## Why are there three downloads?

The model is a pipeline of cooperating components. The ZIP files split that pipeline into manageable downloads; they are not three alternative models. **Download all three.**

| Download | What it contains | Its role |
| --- | --- | --- |
| `sd-turbo-text-encoder.zip` | Text encoder weights and configuration | Converts the prompt’s tokens into numerical representations that guide image generation. |
| `sd-turbo-unet.zip` | The U-Net denoising network | Uses the prompt representation to transform a noisy latent representation toward an image. This is the largest component. |
| `sd-turbo-config-and-vae.zip` | VAE weights, tokenizer, scheduler settings, and pipeline configuration | The tokenizer prepares text for the encoder; the scheduler configures the denoising step; the VAE decoder turns the resulting latent representation into visible pixels. |

The combined download is approximately **2.58 GB**. This is download size, not total GPU memory usage: running the model also requires memory for intermediate calculations and application resources.

## How does an image model produce LiveGrid’s live visuals?

LiveGrid continuously varies the latent noise supplied to SD-Turbo while keeping your prompt as the visual direction. The model generates related images, and a separate output loop blends successive images into a live video feed.

That feed is enlarged to **1080 × 1080** and arranged as a **10 × 10 grid**. Mosaic mode spreads one image across the squares; Repeat mode shows the same image in each square. The 100 squares share one generation stream—they are not 100 separate AI models.

This is **evolving image synthesis**, not a model trained to generate temporally consistent video. It works well for exploring abstract textures and morphing forms. Stable characters, realistic physical motion, precise typography, and deliberate camera movement are not guaranteed. Enlarging the output also does not add native 1080-pixel AI detail.

The browser panel controls the local engine. TouchDesigner and MadMapper receive and arrange its output; the GitHub website does not perform inference. Running these weights locally uses GPU resources, not an OpenAI API key or API tokens.

## Install the weights

1. Download the LiveGrid application separately from the [project site](https://projectionheart.github.io/livegrid-generative-ai/) and install its Python dependencies.
2. Download all three model ZIP files from this release.
3. Extract each ZIP into your **LiveGrid folder**, merging the `models/sd-turbo/` folders. Avoid creating an extra enclosing directory.
4. Confirm that `LiveGrid/models/sd-turbo/model_index.json` exists alongside the `text_encoder`, `unet`, `vae`, `tokenizer`, and `scheduler` folders.
5. Restart LiveGrid. It will use this local model instead of downloading the model from Hugging Face.

After dependencies and model files are installed, generation can run offline on a compatible Windows computer with an NVIDIA CUDA GPU. The packaged model was tested by extracting these archives and successfully generating an image with model downloads disabled.

## Provenance and verification

Source: [`stabilityai/sd-turbo`](https://huggingface.co/stabilityai/sd-turbo), revision `b261bac6fd2cf515557d5d0707481eafa0485ec2`.

All three tensor files were checked against the upstream SHA-256 hashes. The uploaded ZIP checksums also match the values in `MODEL-MANIFEST.json`.

The tensor weights are unmodified. Original developer filesystem paths in configuration metadata were replaced with the public model identifier. These archives contain no LiveGrid user prompts, local settings, generated images, or credentials. Verification establishes that the tensor files match the published upstream model; it is not an audit of that model’s training data.

## License and attribution

The weights are distributed under the **Stability AI Community License**, included with an attribution notice in every archive. Model licensing is separate from the LiveGrid code and any TouchDesigner or MadMapper license. Read the included agreement for its commercial-use requirements and restrictions.

For the model’s training approach, intended uses, and limitations, see the [official SD-Turbo model card](https://huggingface.co/stabilityai/sd-turbo).
