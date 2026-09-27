#!/usr/bin/env node
/*
 * Studio product photos (no person, white background) for the garments the skole store
 * has none of: shorts, singlet and the college jacket. The product cards and pages show
 * the skole store's ghost-mannequin shots (~/skole/assets/skole_*_{front,back}.jpg) for
 * the rest, so these copy their look: the garment from our own on-model photo, the
 * style, light and framing from a skole shot.
 *
 *   node _source/product_shots.mjs --dry-run             # print prompts, spend nothing
 *   node _source/product_shots.mjs                       # all of them
 *   node _source/product_shots.mjs --only singlet
 *
 * Writes _source/product-shots/<name>.png (gitignored); make_shop_images.py turns them
 * into img/shop/*.webp. The key is read from ~/skole/scripts/.env, as model_photos.mjs does.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const S = dirname(fileURLToPath(import.meta.url));
const SKOLE = join(homedir(), "skole");
const OUT = join(S, "product-shots");
const argv = process.argv.slice(2);
const DRY = argv.includes("--dry-run");
const ONLY = argv.includes("--only") ? argv[argv.indexOf("--only") + 1].split(",") : null;
const SIZE = "1536x1536";

const env = Object.fromEntries(
  readFileSync(join(SKOLE, "scripts/.env"), "utf8").split(/\r?\n/).filter((l) => /^[A-Z_]+=/.test(l))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1).trim()]));
if (!DRY && !env.OPENAI_API_KEY) throw new Error("OPENAI_API_KEY missing from ~/skole/scripts/.env");

/* Short, and the photographs carry the garment (Alexander's rule for these prompts). */
const shot = (what, extra = "") =>
  `Ghost mannequin product photo of the exact ${what} from the first photo, front view, filled out as if worn by an ` +
  `invisible body, centred and square on a plain white background, in the same style and light as ` +
  `the second photo.${extra ? " " + extra : ""} No person, no skin, no shoes, no logo, no text.`;

const SPEC = {
  "shorts-unisex": {
    refs: [join(S, "model-photos/shorts-unisex.png"), join(SKOLE, "assets/skole_bukse_unisex_graa_front.jpg")],
    prompt: shot("light heather grey sweat shorts", "They end just above the knee; the white waist drawcord hangs loose."),
  },
  "shorts-dame": {
    refs: [join(S, "model-photos/shorts-dame.png"), join(SKOLE, "assets/skole_bukse_dame_graa_front.jpg")],
    prompt: shot("women's light heather grey sweat shorts", "A short leg ending at mid-thigh; the white waist drawcord hangs loose."),
  },
  singlet: {
    refs: [join(S, "model-photos/singlet.png"), join(SKOLE, "assets/skole_tshirt_hvit_front.jpg")],
    prompt: shot("bright white singlet (tank top)"),
  },
  collegejakke: {
    refs: [join(S, "model-photos/collegejakke.png"), join(SKOLE, "assets/skole_ziphoodie_navy_front.jpg")],
    prompt: shot("college jacket",
      "Navy body, pure white sleeves, the collar, the snaps closed, the striped rib cuffs and hem, and one large cream " +
      "chenille letter F on the chest, reading the right way round, exactly as in the first photo.").replace(", no text.", "."),
  },
};

const mime = (f) => (f.endsWith(".webp") ? "image/webp" : f.endsWith(".png") ? "image/png" : "image/jpeg");
async function generate(prompt, files) {
  const form = new FormData();
  for (const [k, v] of Object.entries({ model: "gpt-image-2", prompt, size: SIZE, quality: "high", n: "1", output_format: "png" })) form.append(k, v);
  for (const f of files) form.append("image[]", new Blob([readFileSync(f)], { type: mime(f) }), f.split("/").pop());
  const r = await fetch("https://api.openai.com/v1/images/edits", { method: "POST", headers: { Authorization: `Bearer ${env.OPENAI_API_KEY}` }, body: form });
  const j = await r.json();
  if (!r.ok) throw new Error(`${r.status} ${JSON.stringify(j.error || j).slice(0, 300)}`);
  return { buf: Buffer.from(j.data[0].b64_json, "base64"), usage: j.usage };
}
async function withRetry(label, fn) {
  const wait = [5000, 20000, 60000];
  for (let i = 0; ; i++) {
    try { return await fn(); } catch (e) {
      console.error(`  ${label}: attempt ${i + 1} failed: ${e.message}`);
      if (i >= wait.length || /credit|billing|quota/i.test(e.message)) throw e;
      await new Promise((s) => setTimeout(s, wait[i]));
    }
  }
}

mkdirSync(OUT, { recursive: true });
const names = ONLY || Object.keys(SPEC);
for (const n of names) {
  if (!SPEC[n]) throw new Error(`unknown ${n}; one of ${Object.keys(SPEC).join(", ")}`);
  const missing = SPEC[n].refs.filter((f) => !existsSync(f));
  if (missing.length) throw new Error(`${n}: missing reference ${missing.join(", ")}`);
}
if (DRY) {
  for (const n of names) console.log(`\n${n}\n  refs: ${SPEC[n].refs.map((f) => f.split("/").pop()).join(", ")}\n  ${SPEC[n].prompt}`);
} else {
  let tokens = 0;
  await Promise.all(names.map(async (n) => {
    const res = await withRetry(n, () => generate(SPEC[n].prompt, SPEC[n].refs));
    writeFileSync(join(OUT, `${n}.png`), res.buf);
    tokens += res.usage?.total_tokens || 0;
    console.log(`  ${n}.png ${res.buf.length} bytes`);
  }));
  console.log(`done -> ${OUT} (${tokens} tokens billed)`);
}
