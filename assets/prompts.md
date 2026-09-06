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

---

# Site assets, as installed

Mode: local ComfyUI. `krea2_turbo_bf16` + `krea2_darkbrush` LoRA at 0.8,
Qwen3-VL text encoder, `qwen_image_vae`, 8 steps, cfg 1.0, euler/simple.

Two facts about this setup shaped every prompt below, and both were learned the
hard way:

- **cfg is 1.0, so the negative prompt is never applied.** Classifier-free
  guidance is off; the negative conditioning is computed and discarded. Anything
  that has to be excluded must be excluded by describing what is there instead.
- **A negation inside the positive prompt does the opposite of what it says.**
  "no bottle, no jar" puts *bottle* and *jar* into the conditioning. Four
  attempts at the vapour cell failed exactly this way. The prompt that worked
  names only the object that should exist.

Prompts are written as fields, not prose, matching the base's own two records
above. Every image below was reviewed against its description before install.


## vapor-cell.png

*hero — replaces the base's glass-w.png*  
`size=1536x1024  seed=533753314`

```
Use case: stylized-concept
Asset type: hero artwork for a research portfolio on optically pumped magnetometry
Primary request: A wide 1536x1024 photorealistic macro studio photograph of a rubidium vapour cell.
Scene/backdrop: Light dove-gray seamless studio sweep, nothing else in frame.
Subject: A single small sealed borosilicate glass cell, a squat cylinder about 25 mm across and 25 mm tall with flat polished optical windows on its two circular ends and a short narrow glass stem, the tip-off, standing up from the shoulder. The glass is clear and empty-looking; one tiny bright bead of liquid metal rests in the bottom corner. Thin wall, visible seam where the stem was fused.
Composition/framing: Wide landscape 3:2; the cell centred, occupying about 45 percent of the frame, seen slightly from above at a three-quarter angle.
Lighting/mood: Minimalist premium studio art direction; soft broad key from upper left, gentle rim light picking out the glass edges and the stem.
Materials/textures: Clear thin-walled laboratory glass with true refraction and caustics, one small mercury-like droplet, no coatings, no metal fittings.
Constraints: No chrome clamps, no holder, no mount, no cables, no text, no watermark, no extra objects.
```

## optics-bench.png

*brand scene and about — replaces the base's concrete-courtyard.png*  
`size=1536x1024  seed=1222921344`

```
Use case: photorealistic-natural
Asset type: editorial image for a research portfolio on optically pumped magnetometry
Primary request: A wide 1536x1024 black-and-white fine-grain editorial photograph, crisp contrast, deep blacks, fine monochrome film grain of a laser optics bench, looking straight down its length.
Scene/backdrop: A black anodised aluminium optical breadboard filling the lower half, its regular grid of tapped mounting holes running away from camera to a bright empty far wall.
Subject: Two parallel rows of identical kinematic mirror mounts on short posts, each a small square anodised plate with three adjustment screws and a round mirror held at forty-five degrees; the rows recede and converge.
Composition/framing: Wide landscape 3:2, camera at bench height on the centre line, strong one-point perspective, the far end bright and empty.
Lighting/mood: Even diffuse laboratory light, deep shadow under the mounts, no flare.
Materials/textures: Matte black anodised aluminium, knurled steel adjusters, first-surface mirrors.
Constraints: No humans, no visible laser beam, no text, no watermark, no cables across the frame.
```

## sensor-housing.png

*project card 2, balanced polarimeter*  
`size=1536x1024  seed=1560511686`

```
Use case: photorealistic-natural
Asset type: editorial image for a research portfolio
Primary request: A wide 1536x1024 black-and-white fine-grain editorial photograph, crisp contrast, deep blacks, fine monochrome film grain of a precision machined aluminium sensor housing.
Scene/backdrop: A clean matte steel workbench, plain and uncluttered, softly out of focus behind.
Subject: One rectangular aluminium housing about 136 mm long, lid removed, lying flat. Inside are milled pockets and a long straight channel running its length, with circular seats at intervals. Counterbored fixing holes along the rim, crisp sharp arrises, fine concentric tool marks on the pocket floors.
Composition/framing: Wide landscape 3:2, camera close and slightly above at a three-quarter angle so the internal channel is visible along its length.
Lighting/mood: Raking light from the left so the machined surfaces show their finish; deep shadow in the pockets.
Materials/textures: Bead-blasted and anodised aluminium, bright cut edges, faint machining witness marks.
Constraints: No humans, no hands, no tools, no text, no engraved markings, no watermark.
```

## shielded-chamber.png

*manifesto background*  
`size=1536x1024  seed=1867086054`

```
Use case: photorealistic-natural
Asset type: editorial background image for a research portfolio
Primary request: A wide 1536x1024 black-and-white fine-grain editorial photograph, crisp contrast, deep blacks, fine monochrome film grain looking into the open end of a cylindrical magnetic shield.
Scene/backdrop: A quiet laboratory, dark surroundings, the shield filling the frame.
Subject: Three nested concentric mu-metal cylinders of decreasing diameter seen end on, their rims stepping inward one behind the next, smooth matte grey metal walls with a fine satin finish, a soft pool of light at the innermost end.
Composition/framing: Wide landscape 3:2, camera on the cylinder axis so the rims form clean concentric circles, the bright innermost opening slightly off centre.
Lighting/mood: One soft light from deep inside; the outer rim falls into near-black.
Materials/textures: Matte annealed mu-metal, no reflections sharp enough to read the room.
Constraints: No humans, no cables, no text, no watermark, no visible equipment inside.
```

## metrology.png

*project card 3, supervised pipeline*  
`size=1536x1024  seed=531248676`

```
Use case: photorealistic-natural
Asset type: editorial laboratory photograph for a research portfolio
Primary request: A wide 1536x1024 photorealistic photograph of dimensional metrology reference standards resting on a granite inspection surface.
Scene/backdrop: A black granite surface plate, its lapped top face flat and slightly matte, filling the lower two thirds of the frame; a dark neutral studio background above it, fading out of focus.
Subject: A short stack of four rectangular steel gauge blocks wrung together into one solid column, their lapped faces mirror-bright; beside them two loose blocks lie flat, and a single precision steel cylinder rests on its side. Every surface is bare polished steel. There is no measuring instrument in the frame.
Composition/framing: Wide landscape frame, low camera close to the plate surface, objects grouped left of centre with open granite to the right; shallow depth of field, the near stack sharp and the background soft.
Lighting/mood: Single soft raking light from the left grazing across the granite so the lapped steel faces read as mirrors against the matte stone; deep quiet shadows.
Materials/textures: Mirror-polished hardened steel, fine-grained black granite, faint reflections of the steel in the plate.
Constraints: Absolutely NO dials, NO gauge faces, NO round instrument heads, NO clock-like objects, NO needles or pointers, NO calipers, NO micrometers, NO rulers, NO graduation marks, NO engraved scales. No text, no numbers, no lettering of any kind, no logos, no watermark, no hands, no people.
```

## svc-1-optics.png

*service row S/001, optical path*  
`size=1024x1024  seed=1990473205`

```
Use case: photorealistic-natural
Asset type: small square symbol image for a service row
Primary request: A Square 1024x1024 black-and-white fine-grain editorial photograph, crisp contrast, deep blacks, fine monochrome film grain, macro, of two optical prisms.
Scene/backdrop: Plain very light grey background, no surface texture, nothing else in frame.
Subject: One right-angle prism standing on its square end with the long hypotenuse face toward camera, and beside it a polarising beamsplitter cube of the same height with a faint diagonal seam visible through the glass where its two halves are cemented.
Composition/framing: Square, both pieces centred together, filling about 65 percent of the frame, eye level.
Lighting/mood: Soft even light with one narrow specular highlight along each polished edge.
Materials/textures: Clear optical glass with sharp ground bevels and honest refraction.
Constraints: No mounts, no holders, no text, no watermark, no rainbow colour fringing.
```

## svc-2-vapour.png

*service row S/002, atomic physics*  
`size=1024x1024  seed=96677971`

```
Use case: photorealistic-product
Asset type: close-up laboratory hardware photograph for a research portfolio
Primary request: A square 1024x1024 photorealistic macro studio photograph of a sealed glass ampoule used as a rubidium vapour cell, a solid closed capsule of laboratory glass.
Scene/backdrop: Light dove-gray seamless studio sweep.
Subject: One small hermetically sealed borosilicate glass ampoule standing upright, a squat capsule about 25 mm across and 25 mm tall. Its top is closed by a smoothly domed glass cap, the way the fused end of a flame-sealed ampoule is domed, so the capsule is one continuous unbroken volume of glass from the flat base to the dome. A short narrow glass tip-off stem about 6 mm long, drawn to a rounded fused point, rises at an angle from the shoulder where the dome meets the wall. The wall is thin and continuous. Inside the sealed volume a single tiny bright bead of liquid metal rests in the bottom corner, and a faint fusion seam marks the tip-off.
Composition/framing: Square frame, three-quarter view from slightly above; the ampoule centred, occupying about 55 percent of the frame.
Lighting/mood: Minimalist premium studio art direction; soft broad key from the upper left, gentle rim light along the glass edges and the stem, soft contact shadow.
Materials/textures: Clear thin-walled laboratory glass with true refraction and caustics, faint green edge tint at the thickest glass, one small mercury-like droplet.
```

## svc-3-machining.png

*service row S/003, parametric CAD*  
`size=1024x1024  seed=789506173`

```
Use case: photorealistic-product
Asset type: close-up manufacturing photograph for a research portfolio
Primary request: A square 1024x1024 photorealistic close-up of a finished precision-machined aluminium part sitting still on a workbench, already cut, with no tool touching it.
Scene/backdrop: A dark matte steel bench top, clean and swept, softly out of focus behind the part.
Subject: ONE rectangular block of aluminium, its top face freshly face-milled to a smooth continuous surface covered in fine regular overlapping arcs of tool witness marks. A shallow circular pocket with a clean vertical wall and a flat bottom is milled into the top face, and two small precisely drilled holes with crisp unbroken edges sit beside it. All outer edges are sharp, straight and lightly chamfered.
Composition/framing: Square frame, three-quarter view from about 40 degrees above so the milled top face and one side wall are both visible; the block fills about 65% of the frame.
Lighting/mood: Raking light from the upper left so the concentric tool marks catch the light as fine parallel highlights; controlled specular sheen, soft shadow.
Materials/textures: Bare satin aluminium with a fine directional machined finish, sharp chamfers, no coating, no paint.
Constraints: The part is finished and untouched. NO cutting tool, NO end mill, NO drill bit, NO spindle, NO chips or swarf, NO coolant, NO torn or fractured or broken material, NO jagged edges, NO cracks, NO rough cast surface. No text, no numbers, no watermark, no hands.
```

## svc-4-detectors.png

*service row S/004, detection*  
`size=1024x1024  seed=774088898`

```
Use case: photorealistic-natural
Asset type: small square symbol image for a service row
Primary request: A Square 1024x1024 black-and-white fine-grain editorial photograph, crisp contrast, deep blacks, fine monochrome film grain, macro, of a matched pair of photodiode detectors.
Scene/backdrop: Plain very light grey background, nothing else in frame.
Subject: Two identical small cylindrical metal-can photodiodes on short posts, standing side by side at the same height, each with a round flat glass window at the front and a small square active area visible behind the glass.
Composition/framing: Square, the pair centred and symmetrical, facing camera, filling about 60 percent of the frame.
Lighting/mood: Soft even light; a matching highlight on each window.
Materials/textures: Nickel-plated metal cans, clear glass windows, matte black posts.
Constraints: No cables, no connectors in frame, no text, no part numbers, no watermark.
```

## svc-5-inspection.png

*service row S/005, inspection*  
`size=1024x1024  seed=1359601664`

```
Use case: photorealistic-natural
Asset type: small square symbol image for a service row
Primary request: A Square 1024x1024 black-and-white fine-grain editorial photograph, crisp contrast, deep blacks, fine monochrome film grain, seen from directly above, of parts laid out for inspection.
Scene/backdrop: A matte dark inspection tray filling the frame.
Subject: Twenty-five identical small machined aluminium parts arranged in a precise five by five grid, each in its own shallow recess, all facing the same way, evenly spaced.
Composition/framing: Square, straight top-down view, the grid square to the frame and filling about 80 percent of it.
Lighting/mood: Flat even overhead light so every part reads the same; short soft shadows.
Materials/textures: Bead-blasted aluminium parts, matte dark tray.
Constraints: No humans, no hands, no tools, no text, no labels, no watermark.
```

---

# Service-row images, redrawn with Ideogram 4

Mode: local ComfyUI, `ideogram4_bf16` + `ideogram4_unconditional_bf16` through
`DualModelGuider` at cfg 7, `qwen3vl_8b_bf16` text encoder, `flux2-vae`,
`Ideogram4Scheduler` Quality preset (48 steps, mu 0.0, std 1.5), euler,
1024x1024. The bf16 weights were dequantized locally from the published
fp8_scaled files: MPS cannot hold a `Float8_e4m3fn` tensor at all, so every
published Ideogram 4 variant fails on Apple Silicon.

Two things about this model shaped the prompts, and both cost a round to learn:

- **Prompts must be structured JSON, not prose.** Ideogram 4.0's built-in safety
  filter has a much higher false-positive rate on plain text — the ComfyUI
  template says so outright. Three of five field-style prompts came back as
  `Image blocked by safety filter`; removing the negative prompt changed
  nothing, and rewriting the same content as the JSON caption contract cleared
  two of the three immediately.
- **The filter also judges the rendered image, not only the text.** The vapour
  cell stayed blocked in JSON. Four variants changed one thing each: the
  plainest wording with an upright full silhouette was blocked, while the same
  subject cropped, mounted, or laid on its side all passed. The silhouette is
  what it objects to, so S/002 is shot seated in its holder.

Counts are the other known weakness. Six holes came out as eight twice, and a
five-by-five grid came out four-by-five then four-by-four. Asking harder did not
work; S/003 and S/005 are framed so the repeated features run off the frame edge
and no count is assertable.

Contract: exactly three top-level keys, minified, `bbox` as `[y1, x1, y2, x2]`
normalised 0-1000 from a top-left origin, one coherent subject per element.

## svc-1-optics.png

*service row S/001, optical path*  
`size=1024x1024  seed=7685860265279240  preset=Quality`

```json
{
  "aspect_ratio": "1:1",
  "high_level_description": "A right-angle glass prism and a polarising beamsplitter cube standing side by side on a pale grey studio sweep, black-and-white fine-grain macro product photograph.",
  "compositional_deconstruction": {
    "background": "A smooth pale grey seamless studio sweep, evenly lit, entirely featureless, with one soft contact shadow falling to the lower right.",
    "elements": [
      {
        "type": "obj",
        "bbox": [
          420,
          190,
          770,
          470
        ],
        "desc": "A right-angle prism of water-clear optical glass resting on one square face, its 45-degree hypotenuse turned toward the camera and working as a mirror, every ground edge carrying one narrow uniform bevel that catches a bright hairline, a sharp caustic pooling on the sweep beneath it, rendered in monochrome."
      },
      {
        "type": "obj",
        "bbox": [
          420,
          500,
          770,
          780
        ],
        "desc": "A polarising beamsplitter cube of water-clear optical glass the same height as the prism, built from two right-angle prisms cemented together so one fine straight diagonal seam runs corner to corner through the glass and stays visible from the front, its outer faces darkened evenly by an anti-reflection coating, rendered in monochrome."
      }
    ]
  }
}
```

## svc-2-vapour.png

*service row S/002, atomic physics*  
`size=1024x1024  seed=2002306702012535  preset=Quality`

```json
{
  "aspect_ratio": "1:1",
  "high_level_description": "A sealed borosilicate glass cell seated in a machined aluminium holder on a pale grey studio sweep, black-and-white fine-grain macro photograph of laboratory hardware.",
  "compositional_deconstruction": {
    "background": "A smooth pale grey seamless studio sweep, evenly lit, entirely featureless, with one soft contact shadow falling to the lower right.",
    "elements": [
      {
        "type": "obj",
        "bbox": [
          430,
          300,
          830,
          700
        ],
        "desc": "One machined aluminium holder, a rectangular block with a circular seat milled into its top face and two counterbored fixing holes. Every face is clean bare satin aluminium, uniform and unmarked, carrying nothing but fine even face-mill witness marks, with one narrow chamfer along every edge. Rendered in monochrome."
      },
      {
        "type": "obj",
        "bbox": [
          210,
          380,
          560,
          620
        ],
        "desc": "One small sealed component of clear borosilicate laboratory glass sitting in the holder's circular seat, a squat cylinder as wide as it is tall with a straight thin side wall, a flat base, and a top closing in one smooth continuous dome, forming a single unbroken sealed volume of glass with no opening anywhere; one short narrow stem rises at an angle from the shoulder and is drawn down to a rounded solid fused point. The glass is empty and clean, with true refraction against the aluminium. Rendered in monochrome."
      }
    ]
  }
}
```

## svc-3-machining.png

*service row S/003, parametric CAD*  
`size=1024x1024  seed=8352767430678811  preset=Quality`

```json
{
  "aspect_ratio": "1:1",
  "high_level_description": "An extreme macro close-up across the finish-milled face of an aluminium part, its counterbored holes running out past the frame edge, black-and-white fine-grain product photograph.",
  "compositional_deconstruction": {
    "background": "The milled aluminium face itself fills the whole frame, falling out of focus toward the top where a pale grey studio sweep shows in a narrow band.",
    "elements": [
      {
        "type": "obj",
        "bbox": [
          120,
          0,
          1000,
          1000
        ],
        "desc": "The top face of a bare satin aluminium part seen in extreme macro from a low raking angle, so close that the part's outline is far outside the frame. The surface is covered in fine regular overlapping arcs of face-mill witness marks catching the raking light as parallel highlights. A shallow circular pocket with a clean vertical wall and a flat floor sits at the lower left. Counterbored holes with crisp unbroken edges curve away from that pocket toward the upper right and continue off the right edge of the frame, the nearest hole sharp and the farthest already soft. One narrow uniform chamfer runs along a machined step crossing the lower right corner. No tool touches the part. Rendered in monochrome."
      }
    ]
  }
}
```

## svc-4-detectors.png

*service row S/004, signal and validation*  
`size=1024x1024  seed=6868208227789809  preset=Quality`

```json
{
  "aspect_ratio": "1:1",
  "high_level_description": "Two identical metal-can photodiode detectors standing upright side by side on a pale grey studio sweep, black-and-white fine-grain macro product photograph of matched electronic components.",
  "compositional_deconstruction": {
    "background": "A smooth pale grey seamless studio sweep, evenly lit, entirely featureless, with one soft contact shadow falling to the lower right.",
    "elements": [
      {
        "type": "obj",
        "bbox": [
          300,
          190,
          800,
          450
        ],
        "desc": "One small cylindrical nickel-plated metal photodiode package standing upright, its rolled rim catching a bright ring highlight, closed by a flat glass window through which one square matte dark silicon die is clearly visible with two hairline bond wires arcing from its corners to the package wall, three straight metal leads dropping from its base out of the bottom of the frame. Rendered in monochrome."
      },
      {
        "type": "obj",
        "bbox": [
          300,
          550,
          800,
          810
        ],
        "desc": "A second photodiode package identical to the first in height, diameter, rim, window and die size, standing upright at the same height and lit identically, its three straight metal leads dropping from its base out of the bottom of the frame. Rendered in monochrome."
      }
    ]
  }
}
```

## svc-5-inspection.png

*service row S/005, supervised pipeline*  
`size=1024x1024  seed=6477864860046536  preset=Quality`

```json
{
  "aspect_ratio": "1:1",
  "high_level_description": "An overhead macro close-up of identical turned steel parts standing in a black foam inspection tray, the grid running off every edge of the frame with one pocket left empty, black-and-white fine-grain photograph.",
  "compositional_deconstruction": {
    "background": "Dense matte black foam fills the entire frame, seen square-on from directly overhead, its milled pockets running past all four frame edges.",
    "elements": [
      {
        "type": "obj",
        "bbox": [
          0,
          0,
          1000,
          1000
        ],
        "desc": "A field of identical short stepped turned steel cylinders standing on end in the milled pockets of a dense matte black foam tray, seen from directly overhead. The rows run parallel to the frame edges and continue past all four edges, cut off by the frame on every side so neither the tray rim nor the extent of the batch is visible. Every part stands at the same height and the same orientation, each with a bright polished top face carrying fine concentric lathe marks and one small concentric bore at its centre. One pocket left of the frame centre is empty, its bare foam floor visible, the part that belongs there removed for measurement. A small crisp shadow sits inside every pocket. Rendered in monochrome."
      }
    ]
  }
}
```
