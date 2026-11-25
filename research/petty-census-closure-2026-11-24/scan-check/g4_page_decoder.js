// CCITT Group 4 (T.6) decoder with block downsampling, a 1-bit PNG encoder, and a minimal PDF image extractor.
// Written for ProQuest's scanned PDFs (one CCITT image per page). Runs in the browser and in Node.
(function (root) {
  const WT = "00110101 000111 0111 1000 1011 1100 1110 1111 10011 10100 00111 01000 001000 000011 110100 110101 101010 101011 0100111 0001100 0001000 0010111 0000011 0000100 0101000 0101011 0010011 0100100 0011000 00000010 00000011 00011010 00011011 00010010 00010011 00010100 00010101 00010110 00010111 00101000 00101001 00101010 00101011 00101100 00101101 00000100 00000101 00001010 00001011 01010010 01010011 01010100 01010101 00100100 00100101 01011000 01011001 01011010 01011011 01001010 01001011 00110010 00110011 00110100".split(" ");
  const WM = "11011 10010 010111 0110111 00110110 00110111 01100100 01100101 01101000 01100111 011001100 011001101 011010010 011010011 011010100 011010101 011010110 011010111 011011000 011011001 011011010 011011011 010011000 010011001 010011010 011000 010011011".split(" ");
  const BT = "0000110111 010 11 10 011 0011 0010 00011 000101 000100 0000100 0000101 0000111 00000100 00000111 000011000 0000010111 0000011000 0000001000 00001100111 00001101000 00001101100 00000110111 00000101000 00000010111 00000011000 000011001010 000011001011 000011001100 000011001101 000001101000 000001101001 000001101010 000001101011 000011010010 000011010011 000011010100 000011010101 000011010110 000011010111 000001101100 000001101101 000011011010 000011011011 000001010100 000001010101 000001010110 000001010111 000001100100 000001100101 000001010010 000001010011 000000100100 000000110111 000000111000 000000100111 000000101000 000001011000 000001011001 000000101011 000000101100 000001011010 000001100110 000001100111".split(" ");
  const BM = "0000001111 000011001000 000011001001 000001011011 000000110011 000000110100 000000110101 0000001101100 0000001101101 0000001001010 0000001001011 0000001001100 0000001001101 0000001110010 0000001110011 0000001110100 0000001110101 0000001110110 0000001110111 0000001010010 0000001010011 0000001010100 0000001010101 0000001011010 0000001011011 0000001100100 0000001100101".split(" ");
  const XM = "00000001000 00000001100 00000001101 000000010010 000000010011 000000010100 000000010101 000000010110 000000010111 000000011100 000000011101 000000011110 000000011111".split(" ");
  function table(term, makeup) {
    const m = new Map();
    term.forEach((c, i) => m.set(c, i));
    makeup.forEach((c, i) => m.set(c, 64 * (i + 1)));
    XM.forEach((c, i) => m.set(c, 1792 + 64 * i));
    return m;
  }
  const WHITE = table(WT, WM), BLACK = table(BT, BM);
  // code maps keyed by (length, value) for speed
  function keyed(m) { const k = new Map(); for (const [c, v] of m) k.set(c.length * 65536 + parseInt(c, 2), v); return k; }
  const WK = keyed(WHITE), BK = keyed(BLACK);

  function decodeG4(data, cols, rows, blackIs1, onRow) {
    let pos = 0; const nbits = data.length * 8;
    const bit = () => { if (pos >= nbits) { pos++; return 0; } const b = (data[pos >> 3] >> (7 - (pos & 7))) & 1; pos++; return b; };
    const peekMode = () => {
      // returns mode code: P,H,V0,VR1..3,VL1..3,EOL/ERR
      let v = 0;
      for (let len = 1; len <= 7; len++) {
        v = (v << 1) | bit();
        if (len === 1 && v === 1) return 'V0';
        if (len === 3) { if (v === 3) return 'VR1'; if (v === 2) return 'VL1'; if (v === 1) return 'H'; }
        if (len === 4 && v === 1) return 'P';
        if (len === 6) { if (v === 3) return 'VR2'; if (v === 2) return 'VL2'; }
        if (len === 7) { if (v === 3) return 'VR3'; if (v === 2) return 'VL3'; }
      }
      return 'ERR';
    };
    const run = (K) => {
      let total = 0;
      for (;;) {
        let v = 0, len = 0, got = -1;
        while (len < 13) { v = (v << 1) | bit(); len++; const r = K.get(len * 65536 + v); if (r !== undefined) { got = r; break; } }
        if (got < 0) return -1;
        total += got;
        if (got < 64) return total;
      }
    };
    let ref = [cols, cols];
    for (let y = 0; y < rows; y++) {
      const cur = [];
      let a0 = -1, color = 0, i = 0; // color 0 = white
      while (a0 < cols) {
        // b1: first changing element on ref to the right of a0 whose color is opposite to `color`
        i = Math.max(0, i - 2);
        while (i < ref.length - 2 && ref[i] <= a0) i++;
        if ((i & 1) !== color) i++;
        const b1 = i < ref.length ? ref[i] : cols, b2 = i + 1 < ref.length ? ref[i + 1] : cols;
        const mode = peekMode();
        if (mode === 'ERR') { onRow(y, cur, true); return y; }
        if (mode === 'P') { a0 = b2; continue; }
        if (mode === 'H') {
          const r1 = run(color === 0 ? WK : BK), r2 = run(color === 0 ? BK : WK);
          if (r1 < 0 || r2 < 0) { onRow(y, cur, true); return y; }
          const s = a0 < 0 ? 0 : a0;
          const a1 = Math.min(s + r1, cols), a2 = Math.min(a1 + r2, cols);
          cur.push(a1, a2); a0 = a2;
          continue;
        }
        const d = { V0: 0, VR1: 1, VR2: 2, VR3: 3, VL1: -1, VL2: -2, VL3: -3 }[mode];
        const a1 = Math.min(Math.max(b1 + d, 0), cols);
        cur.push(a1); a0 = a1; color ^= 1;
      }
      onRow(y, cur, false);
      ref = cur.concat([cols, cols]);
    }
    return rows;
  }

  // Render a G4 image downsampled by integer factor f into a 1-bit bitmap (1 = black)
  function renderDown(data, W, H, f, threshold) {
    const w = Math.floor(W / f), h = Math.floor(H / f);
    const acc = new Uint16Array(w * h);
    let err = false;
    decodeG4(data, W, H, false, (y, ch, bad) => {
      if (bad) err = true;
      const oy = Math.floor(y / f); if (oy >= h) return;
      const base = oy * w;
      // black runs are [ch[0],ch[1]), [ch[2],ch[3]) ...
      for (let k = 0; k + 1 <= ch.length; k += 2) {
        const s = ch[k], e = k + 1 < ch.length ? ch[k + 1] : W;
        for (let x = s; x < e; x++) { const ox = (x / f) | 0; if (ox < w) acc[base + ox]++; }
      }
    });
    const lim = Math.max(1, Math.round(f * f * threshold));
    const out = new Uint8Array(w * h);
    for (let j = 0; j < w * h; j++) out[j] = acc[j] >= lim ? 1 : 0;
    return { w, h, px: out, err };
  }

  let CRC = null;
  function crc32(buf) {
    if (!CRC) { CRC = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; CRC[n] = c >>> 0; } }
    let c = 0xffffffff; for (let i = 0; i < buf.length; i++) c = CRC[(c ^ buf[i]) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0;
  }
  async function deflate(u8) { const cs = new CompressionStream('deflate'); const w = cs.writable.getWriter(); w.write(u8); w.close(); return new Uint8Array(await new Response(cs.readable).arrayBuffer()); }
  async function png1(bm) {
    const rb = Math.ceil(bm.w / 8), raw = new Uint8Array((rb + 1) * bm.h);
    for (let y = 0; y < bm.h; y++) {
      const o = y * (rb + 1); raw[o] = 0;
      for (let x = 0; x < bm.w; x++) if (!bm.px[y * bm.w + x]) raw[o + 1 + (x >> 3)] |= 0x80 >> (x & 7); // 1 = white
    }
    const z = await deflate(raw);
    const chunks = [];
    const chunk = (type, data) => { const len = new Uint8Array(4); new DataView(len.buffer).setUint32(0, data.length); const td = new Uint8Array(4 + data.length); td.set([...type].map(c => c.charCodeAt(0))); td.set(data, 4); const crc = new Uint8Array(4); new DataView(crc.buffer).setUint32(0, crc32(td)); chunks.push(len, td, crc); };
    const ih = new Uint8Array(13); const dv = new DataView(ih.buffer); dv.setUint32(0, bm.w); dv.setUint32(4, bm.h); ih[8] = 1; ih[9] = 0; ih[10] = 0; ih[11] = 0; ih[12] = 0;
    chunks.push(new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]));
    chunk('IHDR', ih); chunk('IDAT', z); chunk('IEND', new Uint8Array(0));
    const n = chunks.reduce((a, c) => a + c.length, 0), out = new Uint8Array(n); let p = 0; for (const c of chunks) { out.set(c, p); p += c.length; } return out;
  }

  // Find image XObjects in object order: [{w,h,filter,k,cols,decodeInv,data}]
  function pdfImages(b) {
    const s = new TextDecoder('latin1').decode(b);
    const out = [];
    const re = /(\d+)\s+0\s+obj\s*<<([\s\S]*?)>>\s*stream\r?\n/g; let m;
    while ((m = re.exec(s))) {
      const dict = m[2];
      if (!/\/Subtype\s*\/Image/.test(dict)) continue;
      const st = m.index + m[0].length;
      const lenm = dict.match(/\/Length\s+(\d+)(\s+0\s+R)?/);
      let en;
      if (lenm && !lenm[2]) en = st + parseInt(lenm[1]); else en = s.indexOf('endstream', st);
      const num = (k) => { const x = dict.match(new RegExp('/' + k + '\\s+(-?\\d+)')); return x ? parseInt(x[1]) : null; };
      out.push({ obj: parseInt(m[1]), w: num('Width'), h: num('Height'), filter: (dict.match(/\/Filter\s*\/(\w+)/) || [])[1] || '', k: num('K') ?? 0, cols: num('Columns'), inv: /\/Decode\s*\[\s*1\s+0\s*\]/.test(dict), bis1: /\/BlackIs1\s+true/.test(dict), data: b.subarray(st, en) });
    }
    out.sort((a, c) => a.obj - c.obj);
    return out;
  }

  async function pagePng(img, targetW, threshold) {
    if (img.filter !== 'CCITTFaxDecode' || img.k >= 0) return { err: 'unsupported ' + img.filter + ' K=' + img.k };
    const f = Math.max(1, Math.round(img.w / targetW));
    const bm = renderDown(img.data, img.w, img.h, f, threshold ?? 0.12);
    if (img.inv !== img.bis1) for (let j = 0; j < bm.px.length; j++) bm.px[j] ^= 1;
    return { png: await png1(bm), w: bm.w, h: bm.h, err: bm.err ? 'decode error' : '' };
  }

  root.G4 = { decodeG4, renderDown, png1, pdfImages, pagePng };
})(typeof window !== 'undefined' ? window : globalThis);
