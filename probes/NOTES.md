# MAG323UPF protocol notes

Monitor ID: s140 = `00\x94`, s150 = `V61`. Probe tool: `tools/probe_reads.py` (read-only, `58<code>` only).
Snapshots: `baseline.json` (initial state), then one JSON per OSD change.

## Verified by OSD change

| Code  | Setting    | Values seen | Notes |
|-------|------------|-------------|-------|
| 00120 | mode       | 010 = user, 001 = fps | matches msigd MAG list |
| 00200 | game_mode  | 000 = user, 001 = fps | matches msigd |

| 002;0 | night_vision | 003 = strongest, 004 = ai (OSD-confirmed) | msigd list off/normal/strong/strongest/ai |
| 00270 | smart_crosshair_icon | 000 = off, 001 = icon1 | newer-model list (off, icon1..icon6), not red1..red6 |
| 00271 | smart_crosshair_color | 000 = white, 001 = red (OSD-confirmed), 002 = auto (initial state; auto rendered red) | matches msigd list white/red/auto; OSD order white, red, auto |
| 00900-00930 | navi_up/down/left/right | up 2 game_mode, down 3 smart_crosshair, left 11 kvm, right 5 input (OSD-confirmed) | matches msigd MAG274QRX list; middle entries (4,6-10) unverified |

Pattern so far: every verified value matches msigd's newer-model (MAG274QRX/MPG273CQR-style) tables.
Candidate base for MAG323UPF support: MAG274QRX settings, minus codes that time out here.

Codes use ASCII 0x30-0x3f per digit (`:;<=>?` = 10-15), so `002;0` = sub-code 0x2B0.
Also answering (unverified): 002:0 screen_size 000, 008:0 hdmi_cec 000, 008>0 kvm 000.

FPS preset also set: image_enhancement 000→002, brightness 100→090, sharpness 000→002.

## Not supported (timeout / 56006)

00180 quick_charge, 001f alarm4x, 00460 gray_level, 00480 low_blue_light (timeout);
00650–00690 toggle_display / sound / pbp_input1-3, 00840 reset (56006 on read).

## Write tests (msigd built with ro=false locally)

| Setting    | Write             | Result |
|------------|-------------------|--------|
| brightness | 70 → 60 → 70      | accepted (5600+), read back matched both times |
| game_mode  | user → fps → user | accepted; fps applied preset (brightness 90, sharpness 2, image_enhancement 2, night_vision ai); back to user restored all 80 codes exactly |
| night_vision | off → normal → off | accepted, read back matched |
| smart_crosshair_icon | off → icon1 → off | accepted, read back matched |
| smart_crosshair_color | red → white → red | accepted, read back matched |
| contrast   | 70 → 60 → 70      | accepted, read back matched |
| response_time | fast → normal → fast | accepted, read back matched |
| eye_saver  | off → on → off    | accepted, read back matched |

Batch above: full 80-code diff vs pre-batch snapshot was empty afterwards.
Not yet write-tested (can blank/switch the screen): input, kvm, power, pip/pbp, auto_scan, hdmi_cec.
| auto_scan  | on → off → on     | accepted, read back matched |
| hdmi_cec   | off → on → off    | accepted, read back matched |
| power_button | off → standby → off | accepted, read back matched |
| pip_size   | medium → large → medium (while pip on) | accepted, read back matched |
| pip_position | left_top → right_bottom → left_top (while pip on) | accepted, read back matched |
| pip        | off → pip → off   | accepted, BUT SIDE EFFECT: enabling PiP reset brightness 70→100, response_time fast→normal, free_sync 1→0, zero_latency 1→0; turning PiP off did NOT restore them. frequency read 000 briefly, recovered. |

PiP side effect: a GUI must snapshot settings before enabling PiP/PbP and restore them after. free_sync (00280) and
zero_latency (00290) were restored via OSD, not USB: msigd notes a 00280 write on MAG321CURV hung the monitor.
| input      | dp → hdmi1 → dp   | accepted, read back matched; screen blank ~5 s, DP-3 reconnected |
| kvm        | auto → upstream → auto | accepted, read back matched; monitor HID + C920 stayed on the bus |

NEVER write kvm=type_c from this PC: the monitor's HID control device sits on the monitor's USB hub and would
disconnect, leaving no way to switch back over USB (OSD only).
Writes verified for every MAG323UPF setting we expose except pbp_input/pip_input and refresh/alarm overlays.
