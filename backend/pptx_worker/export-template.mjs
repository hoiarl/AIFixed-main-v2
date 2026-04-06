import fs from 'fs/promises';
import path from 'path';
import Automizer, { ModifyTextHelper, modify } from 'pptx-automizer';

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    const value = argv[i + 1];
    if (key.startsWith('--')) {
      args[key.slice(2)] = value;
      i += 1;
    }
  }
  return args;
}

function ensureArray(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function escapeHtml(text) {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function buildBodyHtml(slide) {
  if (slide.bodyHtml) {
    return slide.bodyHtml;
  }
  const paragraphs = ensureArray(slide.paragraphs);
  const bullets = ensureArray(slide.bullets);
  const parts = ['<html><body>'];
  paragraphs.forEach((paragraph) => {
    parts.push(`<p>${escapeHtml(paragraph)}</p>`);
  });
  if (bullets.length) {
    parts.push('<ul>');
    bullets.forEach((bullet) => parts.push(`<li>${escapeHtml(bullet)}</li>`));
    parts.push('</ul>');
  }
  parts.push('</body></html>');
  return parts.join('');
}

async function loadJson(filePath, fallback = null) {
  if (!filePath) return fallback;
  try {
    const raw = await fs.readFile(filePath, 'utf8');
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function resolveLayoutConfig(config, slideData, index) {
  const layouts = config?.layouts || {};
  const requestedKey = slideData.layoutKey || slideData.kind || (index === 0 ? 'cover' : 'content');
  const layout = layouts[requestedKey] || layouts.content || layouts.cover || {
    sourceSlide: index === 0 ? 1 : 2,
    shapes: {},
  };
  return {
    key: requestedKey,
    sourceSlide: layout.sourceSlide || (index === 0 ? 1 : 2),
    useOriginalLayout: layout.useOriginalLayout !== false,
    shapes: layout.shapes || {},
  };
}

async function setTextShape(slide, selector, text) {
  if (!selector) return false;
  slide.modifyElement(selector, [ModifyTextHelper.setText(String(text ?? ''))]);
  return true;
}

async function setHtmlShape(slide, selector, html) {
  if (!selector) return false;
  slide.modifyElement(selector, modify.htmlToMultiText(html));
  return true;
}

async function applySlideContent(slide, slideData, layoutConfig) {
  const shapes = layoutConfig.shapes || {};
  const elements = await slide.getAllTextElementIds();

  const titleSelector = shapes.title || elements[0] || null;
  const subtitleSelector = shapes.subtitle || null;
  const bodySelector = shapes.body || elements[1] || elements[0] || null;
  const bulletsSelector = shapes.bullets || null;
  const footerSelector = shapes.footer || null;

  const paragraphs = ensureArray(slideData.paragraphs);
  const bullets = ensureArray(slideData.bullets);

  await setTextShape(slide, titleSelector, slideData.title || '');

  if (subtitleSelector) {
    await setTextShape(slide, subtitleSelector, slideData.subtitle || paragraphs[0] || '');
  }

  if (bodySelector) {
    await setHtmlShape(slide, bodySelector, buildBodyHtml(slideData));
  }

  if (bulletsSelector) {
    const bulletHtml = [
      '<html><body><ul>',
      ...bullets.map((item) => `<li>${escapeHtml(item)}</li>`),
      '</ul></body></html>',
    ].join('');
    await setHtmlShape(slide, bulletsSelector, bulletHtml);
  }

  if (footerSelector && slideData.footer) {
    await setTextShape(slide, footerSelector, slideData.footer);
  }
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.input || !args.template || !args.output) {
    throw new Error('Required args: --input <slides.json> --template <template.pptx> --output <out.pptx> [--config <config.json>]');
  }

  const payload = await loadJson(args.input, {});
  const config = await loadJson(args.config, {});
  const slides = ensureArray(payload.slides);
  if (!slides.length) {
    throw new Error('No slides provided');
  }

  const templatePath = path.resolve(args.template);
  const outputPath = path.resolve(args.output);
  const templateDir = path.dirname(templatePath);
  const templateName = path.basename(templatePath);
  const outputDir = path.dirname(outputPath);
  const outputName = path.basename(outputPath);

  const automizer = new Automizer({
    templateDir,
    outputDir,
    removeExistingSlides: true,
    autoImportSlideMasters: true,
  });

  let pres = automizer
    .loadRoot(templateName)
    .load(templateName, 'template');

  slides.forEach((slideData, index) => {
    const layoutConfig = resolveLayoutConfig(config, slideData, index);
    pres = pres.addSlide('template', layoutConfig.sourceSlide, async (slide) => {
      if (layoutConfig.useOriginalLayout) {
        slide.useSlideLayout();
      }
      await applySlideContent(slide, slideData, layoutConfig);
    });
  });

  await pres.write(outputName);
  process.stdout.write(JSON.stringify({ ok: true, output: outputPath }));
}

main().catch((error) => {
  process.stderr.write(String(error?.stack || error?.message || error));
  process.exit(1);
});
