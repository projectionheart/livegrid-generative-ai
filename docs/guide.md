# LiveGrid — generative AI for projection

LiveGrid generates evolving imagery from a text prompt on a local NVIDIA GPU, composes it into 100 squares, and sends a live Spout feed to visual-performance software.

## Current status

- Tested on this Windows laptop: SD-Turbo inference, the browser control panel, and successful Spout sender calls.
- Observed in a short local run: roughly 8–10 generated images/second and 21–22 output frames/second. These are measurements, not guaranteed performance.
- Grid: 10 rows × 10 columns, 1080 × 1080 pixels; each cell is 108 × 108 pixels.
- TouchDesigner reception and MadMapper mapping have **not** been verified. TouchDesigner did not reach a usable editing window during setup. There is no finished native `.toe` or `.mad` project in this package.
- GitHub Pages hosts this documentation. It cannot run CUDA inference or publish Spout textures.

## Start on the current computer

Open **Start LiveGrid.cmd**. The control panel is at http://127.0.0.1:8765. Keep the generator running while using TouchDesigner or MadMapper. Close its console to stop it. If an instance is already running, use its existing panel instead of starting another.

The current computer's launcher can use the prepared environment in `../../work/venv`. For a standalone installation on another computer, follow the next section.

## Install on another Windows computer

1. Install Python 3.12 and a current compatible NVIDIA driver. The tested machine has an NVIDIA RTX 4000 Ada laptop GPU with approximately 12 GB VRAM.
2. Extract the source package into a writable folder.
3. Open **Install on Windows.cmd**. It installs PyTorch with CUDA support and the pinned dependencies into a local `.venv`.
4. Open **Start LiveGrid.cmd**. The first generation run downloads the SD-Turbo model into `models/`. Allow several GB of disk space and an internet connection for initial setup.
5. After the model is cached, inference and controls operate locally. No OpenAI API key or API-token billing is involved.

Do not copy the existing virtual environment to another computer. Recreate it with the installer script. Model licenses and TouchDesigner/MadMapper licenses remain separate from this code; see the model card before commercial use.

## Controls

| Control | Effect |
| --- | --- |
| Prompt / Apply prompt | Changes the visual description for subsequent generated frames |
| Presets | Applies one of three abstract visual descriptions |
| Mosaic | Distributes one evolving image across all 100 cells |
| Repeat | Repeats the same evolving image in every cell |
| Evolution speed | Changes how quickly the latent noise evolves |
| Gap | Adds black separation between cells |
| Brightness | Scales the output intensity |
| Freeze | Holds the image and pauses synthesis |
| Calibration | Sends a numbered 001–100 grid and pauses synthesis |
| Blackout | Sends black and pauses synthesis |

Settings persist locally in `settings.json`. Calibration appears during model startup. The panel reports AI and output rates separately and displays failures rather than silently substituting a different generator.

## What is happening

1. The panel sends control changes to a server bound to `127.0.0.1`; it is not exposed to the local network.
2. Diffusers loads `stabilityai/sd-turbo` in half precision on CUDA. The generation resolution is 512 × 512, with one diffusion step and guidance scale zero.
3. Two random latent tensors are mixed with sine/cosine weights. As the mixture evolves, the model generates related images from the prompt.
4. A separate output loop blends successive images, enlarges them to 1080 × 1080, and applies the selected grid composition.
5. Spout publishes the RGB result as **LiveGrid-AI-100**. A reduced JPEG preview is shown in the browser.

This is evolving image synthesis blended into video, **not a temporal text-to-video model**. Expect morphing and possible flicker. Coherent characters, physical motion, and deliberate camera moves are not guaranteed. The 100 cells share a single generation stream; they are not 100 independently prompted AI generators. The enlarged output does not contain native 1080-pixel AI detail.

## TouchDesigner connection

These steps are prepared for verification in a working TouchDesigner installation:

1. Start LiveGrid first.
2. Add a **Syphon Spout In TOP**. Turn off **Use Spout Active Sender** and select sender **LiveGrid-AI-100**.
3. Connect it to a **Null TOP** named `GRID_100_OUT`. View it and enable Calibration in LiveGrid. Confirm 001 is top-left and 100 bottom-right.
4. To work with cells independently, branch into Crop TOPs using the coordinates in `template/Grid-100.json`. Those coordinates use a top-left origin. TouchDesigner crop controls use bottom/top edges, so convert the vertical coordinates accordingly and check the calibration labels.
5. For MadMapper on this same Windows machine, connect a **Syphon Spout Out TOP** and give it a distinct name such as **LiveGrid-TD-100**, avoiding a feedback loop into the input.
6. For MadMapper on another computer, connect an **NDI Out TOP**, name the source **LiveGrid-TD-100**, and use a wired local network. Enable this output only when ready to send it.
7. Save the verified network as your TouchDesigner project. Native prompt controls inside TouchDesigner remain future work; the working interface is currently the local browser panel.

Spout works only between applications on the same Windows computer. Use NDI for a separate Windows or Mac receiving computer. Do not disable the firewall globally to troubleshoot networking.

## MadMapper handoff

1. Receive **LiveGrid-TD-100** through Spout for a same-computer Windows setup, or through NDI for a second computer.
2. Make a 10 × 10 arrangement of quad surfaces. Set each surface's input selection to its matching cell in the atlas.
3. `template/Grid-100.json` supplies pixel and normalized UV rectangles. `Calibration-100.png` supplies cell labels; `Grid-100.svg` is a visual reference, not a native MadMapper project.
4. Enable live Calibration and align the output corners to the physical surfaces. Keep input crop coordinates fixed while adjusting output geometry.
5. Test blackout, freeze, orientation, all 100 labels, and recovery after restarting the sender; then save the `.mad` project on the mapping computer.

Physical alignment and second-computer reception cannot be verified from this package alone.

## Troubleshooting

- **No CUDA:** verify the NVIDIA driver and run the Windows installer script; CPU generation is not enabled.
- **No Spout source:** keep the generator running and use the same NVIDIA GPU for both programs. Spout does not cross the network.
- **Panel disconnected:** restart LiveGrid, then reload the panel. A public GitHub Pages URL is not the live controller.
- **Port already in use:** an instance may already be running at port 8765. Use it or stop it before starting another.
- **First launch is slow:** model files must download before generation begins.
- **TouchDesigner won't open:** complete its installation and licensing independently; the AI panel can still run without it.

## Checks and sources

`python test_grid.py` checks exact 100-cell coverage, numbering, gap behavior, and invalid-control rejection. Spout sender success was tested; reception in TouchDesigner/MadMapper was not.

- [SD-Turbo model and license](https://huggingface.co/stabilityai/sd-turbo)
- [TouchDesigner Spout input](https://derivative.ca/UserGuide/Syphon_Spout_In_TOP)
- [TouchDesigner NDI output](https://derivative.ca/UserGuide/NDI_Out_TOP)
- [MadMapper media inputs](https://docs.madmapper.com/madmapper/6/3.-media/media-bin)

## GitHub Pages publishing

Repository: `projectionheart/livegrid-generative-ai`.

Publish `docs/` using **Settings → Pages → Deploy from a branch → main → /docs**. The site will normally be available at https://projectionheart.github.io/livegrid-generative-ai/ after GitHub finishes the deployment. This address is an expected destination, not proof of deployment.

Do not commit `models/`, `.venv/`, `settings.json`, logs, or credentials. The downloadable source archive excludes them.
