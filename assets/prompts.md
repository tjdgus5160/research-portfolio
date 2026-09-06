# Original generated website assets

Mode: Built-in image_gen. Exactly one generation per asset; no variants or edits.

## glass-w.png

Use case: stylized-concept
Asset type: original premium development studio website hero artwork
Primary request: A wide 1536x1024 photorealistic 3D studio render of a large angular extruded geometric letter W.
Scene/backdrop: Light dove-gray seamless studio space.
Subject: A single simple original geometric W, transparent solid clear glass with polished chrome edges, floating in space, hard straight angular geometry.
Composition/framing: Wide landscape 3:2 image; object centered and occupies about 60% of the image; three-quarter view, gently tilted.
Lighting/mood: Minimalist premium studio art direction; refined studio lighting, subtle reflected blue on the edges.
Materials/textures: Physically convincing clear glass, polished chrome edging, precise hard geometry.
Constraints: Original simple W, not any existing logo. No extra objects, no extra text, no watermark.

## concrete-courtyard.png

Use case: photorealistic-natural
Asset type: original editorial architectural image for a premium development studio website
Primary request: A wide 1536x1024 black-and-white fine-grain architectural photograph looking upward through a rectangular inner courtyard between monumental modernist concrete office buildings.
Scene/backdrop: Tall monumental concrete office buildings surround a rectangular inner courtyard; central bright empty gray sky.
Composition/framing: Wide landscape 3:2 photograph, camera looking directly upward; strong repeating square windows and converging architectural edges surround the central sky.
Style/medium: Editorial architectural photography, crisp contrast, fine monochrome film grain.
Constraints: No humans, no text, no watermark.

## vapor-cell.png  (replaces glass-w.png)

Mode: local ComfyUI, krea2_turbo_bf16 + krea2_darkbrush LoRA at 0.8, Qwen3-VL
text encoder, 8 steps, cfg 1, euler/simple, 1536x1024. One generation, no
variants or edits.

Use case: stylized-concept
Asset type: hero artwork for a research portfolio on optically pumped magnetometry
Primary request: A wide 1536x1024 photorealistic 3D studio render of a rubidium
vapor cell for an optically pumped magnetometer.
Subject: a small precision cuboid cell of clear glass with polished chrome
mounting collars on two opposing faces, floating in space, hard straight angular
geometry, a faint warm amber glow contained inside the glass.
Scene/backdrop: light dove-gray seamless studio space.
Composition/framing: wide landscape 3:2, object centred and occupying about 55
percent of the frame, three-quarter view, gently tilted.
Lighting/mood: minimalist premium studio art direction, refined studio lighting,
subtle reflected blue on the chrome edges.
Materials/textures: physically convincing clear glass, polished chrome, precise
hard geometry.
Constraints: no text, no watermark, no extra objects.

The art direction deliberately matches glass-w.png — same studio, same
materials, same framing — so the section it sits in is unchanged in everything
but subject.

## optics-bench.png  (replaces concrete-courtyard.png)

Mode: local ComfyUI, krea2_turbo_bf16 + krea2_darkbrush LoRA at 0.8, Qwen3-VL
text encoder, 8 steps, cfg 1, euler/simple, 1536x1024. One generation, no
variants or edits.

Use case: photorealistic-natural
Asset type: editorial image for a research portfolio on optically pumped magnetometry
Primary request: A wide 1536x1024 black-and-white fine-grain photograph of a
laser optics bench in a research laboratory, looking straight down the length of
the bench.
Scene/backdrop: a long optical breadboard with a regular grid of mounting holes,
receding into the distance; rows of identical precision optical mounts,
kinematic mirror mounts, lens holders and posts standing along it in strong
repetition; converging perspective lines toward a bright empty background.
Style/medium: editorial architectural photography treatment, crisp contrast,
deep blacks, fine monochrome film grain, shallow depth of field falling off with
distance.
Constraints: no humans, no text, no watermark, no visible laser beam.

The treatment deliberately matches concrete-courtyard.png — wide monochrome,
fine grain, strong repetition, converging edges, bright centre — because the
same file is cropped three ways in the page and had to behave the same in all
three.

## sensor-housing.png  (balanced-polarimeter card)

Mode: local ComfyUI, krea2_turbo_bf16 + krea2_darkbrush LoRA at 0.8, 8 steps,
cfg 1, euler/simple, 1536x1024. One generation, no variants or edits.

A wide black-and-white fine-grain photograph of a precision machined aluminium
opto-mechanical housing on a workbench, shot close and slightly from above:
milled pockets, counterbored mounting holes, a long internal channel, cover
removed, crisp machined edges and fine tool marks catching the light. Editorial
industrial photography, crisp contrast, deep blacks, fine monochrome film grain,
shallow depth of field. No humans, no text, no watermark, no branding.

## shielded-chamber.png  (manifesto background)

Same model, settings and size.

A wide black-and-white fine-grain photograph looking into the open end of a
cylindrical magnetic shield: nested concentric mu-metal cylinders receding
inward, smooth matte metal walls, a soft pool of light at the far end, strong
concentric geometry and deep shadow around the rim. Editorial architectural
photography treatment, crisp contrast, deep blacks, fine monochrome film grain.
No humans, no text, no watermark.

Both keep the treatment of the image they sit beside, because the page crops
them the same way it cropped the original.

## metrology.png  (supervised-pipeline card)

Same model, settings and size as the others.

A wide black-and-white fine-grain photograph of a precision metrology setup on
a granite surface plate: a stack of steel gauge blocks wrung together, a dial
indicator on a height stand with its probe resting on the stack, and a machined
part beside them awaiting inspection. Editorial industrial photography, crisp
contrast, deep blacks, fine monochrome film grain, shallow depth of field. No
humans, no text, no watermark, no branding.

The card is about separating the side that builds from the side that judges, so
the picture is the act of checking rather than the thing built.

Note: the prompt asked for no legible numbers and the dial still carries its
scale. Nothing on it states a measurement, so it reads as an instrument face
rather than a result — but it is a generated image, not a photograph of a real
reading, and no value on it means anything.
