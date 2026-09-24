# Mobile Controller v1.0.0

A separate, optional phone performance controller in the existing LiveGrid repository.

Hosted controller: https://projectionheart.github.io/livegrid-generative-ai/mobile/

## What it does

- Large phone-friendly prompt presets, brightness, evolution, spacing and layout controls.
- Persistent Freeze and Blackout buttons, plus a calibration switch.
- Authenticated, low-rate live preview from the existing engine.
- An XY pad sending OSC to TouchDesigner, plus mirrored numeric engine controls.
- An explicit demo mode for trying the interface without hardware.

This is a controller, not a browser AI generator or a MIDI device. Image generation and Spout output remain on the Windows computer. OSC was chosen for direct TouchDesigner integration and broad phone-browser support.

## Install the add-on

1. Download `LiveGrid-Mobile-v1.0.0.zip` from this release.
2. Extract its `mobile` and `docs/mobile` folders into your existing LiveGrid folder. The folders are new; the original app.py and index.html are not replaced. The ZIP includes a file list. If installing somewhere else, preserve this relative folder structure and install Python 3.10 or newer.
3. Start your existing LiveGrid engine normally for image controls.
4. Open `mobile/Start Mobile Bridge.cmd`. Leave its window open. No new Python dependencies are required.
5. Put your phone and computer on the same trusted Wi-Fi. Open one of the phone addresses printed by the bridge, such as `http://192.168.1.10:8780`.
6. Expand Connect, enter the private pairing key printed in the bridge window, and connect. The key changes whenever the bridge restarts.

The GitHub Pages interface can open this same local mobile interface: enter the computer's HTTP bridge address and press Connect / open controller. You will then enter the pairing key on the local page. No key is included in the URL or stored in the browser.

Windows may ask to allow Python on the network. For home/studio Wi-Fi, allow only the Private network profile. If it does not ask and the phone cannot connect, allow inbound TCP 8780 for this Python process on Private networks in Windows Firewall. Do not forward this port on your router. Some guest networks isolate devices; use a non-isolated trusted Wi-Fi network. This release does not change firewall settings automatically.

## Stay on the hosted page (optional advanced setup)

An HTTPS page cannot reliably fetch an HTTP Wi-Fi bridge because of browser mixed-content protections. The supported default is to open the locally served controller. To stay on GitHub Pages, provide an HTTPS reverse proxy/tunnel to the bridge at localhost:8780, enter that HTTPS origin and the pairing key on the hosted controller, then connect. The bridge allows the ProjectionHeart Pages origin via CORS. Use `python mobile/bridge.py` without `--lan` when forwarding through a local tunnel; this keeps the listener on loopback. Tunnel installation and hosting are not included in this release.

Local HTTP is unencrypted; use it only on trusted Wi-Fi. Pairing keys grant control and preview access. Never publish or share them. Only static controller assets are public; status, preview and writes require the key. Keys stay in browser memory and the bridge process, not in saved settings.

## TouchDesigner

Video: keep using a Syphon Spout In TOP with sender `LiveGrid-AI-100`.

Control: add an OSC In CHOP, enable Active, set Network Port to **9000**, and leave OSC Address Scope broad enough to receive `/livegrid/*`. The bridge sends float-valued OSC messages over UDP to **127.0.0.1:9000**. You may use `--osc-port` to select a different port. It sends to TouchDesigner on this computer; the existing NDI workflow can still carry video to another computer.

| Address | Range / meaning |
| --- | --- |
| `/livegrid/x` | 0–1, left to right |
| `/livegrid/y` | 0–1, bottom to top |
| `/livegrid/brightness` | 0–1 |
| `/livegrid/speed` | 0.005–0.5 |
| `/livegrid/gap` | 0–30 |
| `/livegrid/layout` | 0 mosaic, 1 repeat |
| `/livegrid/freeze` | 0 off, 1 on |
| `/livegrid/blackout` | 0 off, 1 on |
| `/livegrid/calibrate` | 0 off, 1 on |

Map the incoming X/Y channels to parameters such as displacement amount, hue or transform position. Drag a channel onto the desired parameter and choose Export CHOP, or use a CHOP reference expression. Channel naming depends on your OSC In CHOP prefix settings. XY affects only what you map in TouchDesigner; it does not automatically change the generated image. Prompt text goes to LiveGrid only.

Messages are sent when a control changes. OSC uses UDP and has no delivery acknowledgment. The app reports bridge/engine connectivity, not verified TouchDesigner reception. A reconnect does not replay commands. Blackout is a performance control, not a safety-rated emergency stop. The bridge does not auto-resume or auto-blackout if a phone disconnects; the engine retains its last accepted settings.

## Rollback

**Local:** close the Mobile Bridge window. Use the original controller at http://127.0.0.1:8765/. Its files and engine code are unchanged. Controls you already applied are still the engine's current settings; restore brightness, unfreeze, or clear blackout there if desired. You may remove only the added `mobile` and `docs/mobile` folders to uninstall the add-on.

**Repository/site:** the pre-update tag is `before-mobile-controller-v1.0.0`. The mobile update is a single commit, tagged `mobile-controller-v1.0.0`. To undo it while preserving history, revert that update commit with GitHub or git and push the revert to main. GitHub Pages rebuilds from docs. Avoid resetting the branch or force-pushing, especially after later changes.

## Validation and scope

Automated tests cover authentication, blocked origins, validation, forwarding failure handling, and actual local UDP OSC packets. The UI was checked at phone width with demo controls, keyboard XY and no horizontal overflow. Browser pairing to the local bridge and preview/status from the running LiveGrid engine were also verified. Phone-to-PC Wi-Fi, firewall configuration and reception in the TouchDesigner editor still need to be verified on your equipment. No native .toe project is supplied.

Run tests: `python mobile/test_bridge.py`.

References: [OSC In CHOP](https://derivative.ca/UserGuide/OSC_In_CHOP), [browser mixed content](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Mixed_content).
