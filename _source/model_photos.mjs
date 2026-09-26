#!/usr/bin/env node
/*
 * The on-model product photos the site shows, for the garments the skole store has
 * no photo of (or the wrong one), made with OpenAI gpt-image-2 in the same look as
 * the skole shots: the same model (~/skole/mockups-ref/model-man.png), light grey
 * studio, cropped below the eyes.
 *
 *   node _source/model_photos.mjs --dry-run              # print prompts, spend nothing
 *   node _source/model_photos.mjs                        # all of them
 *   node _source/model_photos.mjs --only hoodie,singlet
 *
 * Writes _source/model-photos/<name>.png (gitignored); make_product_images.py turns
 * them into img/p/<id>-model-*.webp. The key is read from ~/skole/scripts/.env.
 * _source/model-refs/ holds the garment references (factory photos from the Qianshi
 * WhatsApp group; gitignored, they show other groups' designs).
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const S = dirname(fileURLToPath(import.meta.url));
const SKOLE = join(homedir(), "skole");
const OUT = join(S, "model-photos");
const argv = process.argv.slice(2);
const DRY = argv.includes("--dry-run");
const ONLY = argv.includes("--only") ? argv[argv.indexOf("--only") + 1].split(",") : null;
const SIZE = "1536x1536";

const env = Object.fromEntries(
  readFileSync(join(SKOLE, "scripts/.env"), "utf8").split(/\r?\n/).filter((l) => /^[A-Z_]+=/.test(l))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1).trim()]));
if (!DRY && !env.OPENAI_API_KEY) throw new Error("OPENAI_API_KEY missing from ~/skole/scripts/.env");

const MODEL_REF = join(SKOLE, "mockups-ref/model-man.png");
const TORSO = "cropped straight across the lower face so the eyes and nose are out of frame, shown from the mouth down to the hips";
const STUDIO = "on a plain light grey studio backdrop, soft even studio light";
const MAN =
  "The model is a white man in his early twenties with fair skin, clean-shaven, of slim athletic build, and he " +
  "is the same person as in the first reference photograph: the same skin tone, mouth, jawline, hands and build. " +
  "Take ONLY the person from that first photograph; the garment he wears in it is a different product.";
const JOGGERS =
  "Below the waist he wears plain light heather ash grey sweatpants with a short flat white drawcord, the same " +
  "trousers as in the first reference photograph.";
/* Hoodie, zip and college jacket: the person from model-man.png, the garment from a
   photo of it, and a short prompt that lets the photo decide the details. Spelling out
   cord length went wrong both ways (the skole prompts forced them stubby, a length in
   cm made them hang to the pocket; Alexander, 2026-09-26), and the F reference photo
   made the jacket's F come out mirrored, so the F is named in words instead. */
const SAME = "Same crop, pose, light and backdrop as the first photo.";

const SPEC = {
  hoodie: {
    refs: [MODEL_REF, join(SKOLE, "mockups-ref/ref02.png")],
    prompt: `The man from the first photo wearing the grey hoodie from the second photo. ${SAME} No logo, no text.`,
  },
  "zip-hoodie": {
    refs: [MODEL_REF, join(SKOLE, "mockups-ref/ref07.webp")],
    prompt: `The man from the first photo wearing the grey zip hoodie from the second photo, zipped up. ${SAME} No logo, no text.`,
  },
  collegejakke: {
    refs: [MODEL_REF, join(S, "model-refs/collegejakke-front.jpg")],
    prompt:
      "The man from the first photo wearing the college jacket from the second photo, with its collar, pure white " +
      "sleeves and the snaps closed, and one large cream chenille letter F on the chest instead of the SB, the F " +
      `reading the right way round. ${SAME} No other text.`,
  },
  "shorts-unisex": {
    refs: [MODEL_REF, join(SKOLE, "assets/skole_bukse_unisex_life.jpg")],
    prompt:
      `Photo of the legs of a white man in his early twenties wearing light heather ash grey sweat shorts, shown from ` +
      `just above the waistband down to the shoes, with no head, face or chest in frame, ${STUDIO}. ` +
      "The shorts are the same soft fleece fabric and colour as the sweatpants in the second reference photograph, " +
      "with an elastic waistband, a short flat white drawcord hanging a little below the waistband, side pockets and a " +
      "straight leg that ends just above the knee. They are SHORTS, not trousers: the knees and lower legs are bare. " +
      "A real person is wearing them: a little of the bare midriff and one hand are in frame above the waistband. " +
      "He stands with his weight on one leg and wears plain white sneakers with short white socks. The legs are a white " +
      "man's, fair skin, slim athletic build; take only the person from the first reference photograph. No logo, no text.",
  },
  "shorts-dame": {
    refs: [join(SKOLE, "assets/skole_bukse_dame_life.jpg")],
    prompt:
      `Photo of the legs of a young woman wearing women's light heather ash grey sweat shorts, shown from the waist down ` +
      `to the ankles with no head, face or torso above the waist in frame, ${STUDIO}. The shorts are the same soft ` +
      "fleece fabric and colour as the trousers in the reference photograph, a women's cut with a high elastic waist, " +
      "a short flat white drawcord and a relaxed short leg ending at mid-thigh. They are SHORTS: the legs are bare from " +
      "mid-thigh down. She is unmistakably a woman, with white women's sneakers. Same studio, light and framing as the " +
      "reference photograph. No logo, no text.",
  },
  singlet: {
    refs: [MODEL_REF],
    prompt:
      `Photo of a white man in his early twenties wearing a plain bright white cotton jersey tank top (a singlet with ` +
      `shoulder straps about 5 cm wide, a scoop neck and deep armholes, no sleeves), ${TORSO}, ${STUDIO}. ` +
      "He stands with his body turned slightly to his left, both arms relaxed at his sides. " + MAN + " " + JOGGERS +
      " No logo, no text.",
  },
};

const mime = (f) => (f.endsWith(".webp") ? "image/webp" : f.endsWith(".png") ? "image/png" : "image/jpeg");
async function generate(prompt, files) {
  let r;
  if (files.length) {
    const form = new FormData();
    for (const [k, v] of Object.entries({ model: "gpt-image-2", prompt, size: SIZE, quality: "high", n: "1", output_format: "png" })) form.append(k, v);
    for (const f of files) form.append("image[]", new Blob([readFileSync(f)], { type: mime(f) }), f.split("/").pop());
    r = await fetch("https://api.openai.com/v1/images/edits", { method: "POST", headers: { Authorization: `Bearer ${env.OPENAI_API_KEY}` }, body: form });
  } else {
    r = await fetch("https://api.openai.com/v1/images/generations", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.OPENAI_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model: "gpt-image-2", prompt, size: SIZE, quality: "high", n: 1, output_format: "png" }),
    });
  }
  const j = await r.json();
  if (!r.ok) throw new Error(`${r.status} ${JSON.stringify(j.error || j).slice(0, 300)}`);
  return { buf: Buffer.from(j.data[0].b64_json, "base64"), usage: j.usage };
}
async function withRetry(label, fn) {
  const wait = [5000, 20000, 60000];
  for (let i = 0; ; i++) {
    try { return await fn(); } catch (e) {
      console.error(`  ${label}: attempt ${i + 1} failed: ${e.message}`);
      if (i >= wait.length) throw e;
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
  for (const n of names) console.log(`\n${n}\n  refs: ${SPEC[n].refs.map((f) => f.split("/").pop()).join(", ") || "(none)"}\n  ${SPEC[n].prompt}`);
} else {
  let tokens = 0;
  // three at a time; each image takes a minute or two
  for (let i = 0; i < names.length; i += 3) {
    await Promise.all(names.slice(i, i + 3).map(async (n) => {
      const res = await withRetry(n, () => generate(SPEC[n].prompt, SPEC[n].refs));
      writeFileSync(join(OUT, `${n}.png`), res.buf);
      tokens += res.usage?.total_tokens || 0;
      console.log(`  ${n}.png ${res.buf.length} bytes`);
    }));
  }
  console.log(`done -> ${OUT} (${tokens} tokens billed)`);
}
