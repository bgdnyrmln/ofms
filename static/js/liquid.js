/* Home hero: raymarched ferrofluid. A few drops flow into each other in the
   centre; where the pointer actually touches the liquid, a patch of sharp
   spikes slowly rises, like ferrofluid over a magnet.
   Plain WebGL 1, no libraries. Without WebGL the hero keeps its CSS gradient. */
(function () {
  "use strict";

  var canvas = document.querySelector(".hero__gl");
  if (!canvas) return;
  var gl = canvas.getContext("webgl", { antialias: false, alpha: false, depth: false, powerPreference: "high-performance" });
  if (!gl) { canvas.remove(); return; }

  /* ---- the liquid's shape, shared by the shader and the pointer hit test ---- */
  var CY = 0.25, R0 = 0.52, LOBES = 5, K = 0.42;

  var VERT = "attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";

  var FRAG = [
    "#ifdef GL_FRAGMENT_PRECISION_HIGH",
    "precision highp float;",
    "#else",
    "precision mediump float;",
    "#endif",
    "uniform vec2 uRes;",
    "uniform float uTime;",
    "uniform vec3 uP;", // where the pointer touches the surface
    "uniform vec3 uN;", // surface normal there
    "uniform float uS;", // spike strength 0..1
    "const vec3 C = vec3(0.0, " + CY.toFixed(3) + ", 0.0);",
    "vec3 T1, T2;",

    "float smin(float a, float b, float k) {",
    "  float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);",
    "  return mix(b, a, h) - k * h * (1.0 - h);",
    "}",


    // drops orbiting the centre and merging into one mass
    "float body(vec3 p) {",
    "  float t = uTime;",
    "  float d = length(p - C) - " + R0.toFixed(3) + ";",
    "  for (int i = 0; i < " + LOBES + "; i++) {",
    "    float f = float(i);",
    "    vec3 o = C + vec3(sin(t * (0.31 + 0.07 * f) + f * 1.7) * 0.85,",
    "                      cos(t * (0.27 + 0.05 * f) + f * 2.3) * 0.45,",
    "                      sin(t * (0.23 + 0.06 * f) + f) * 0.4);",
    "    d = smin(d, length(p - o) - (0.2 + 0.05 * sin(f * 3.1 + t * 0.5)), " + K.toFixed(3) + ");",
    "  }",
    "  return d + 0.012 * sin(p.x * 5.0 + t * 1.3) * sin(p.y * 4.0 - t) * sin(p.z * 6.0 + t * 0.7);",
    "}",

    // nearest centre of a hexagonal grid: spikes pack like the real Rosensweig pattern
    "vec2 hexCell(vec2 p, float a) {",
    "  vec2 s = vec2(1.0, 1.7320508) * a, h = s * 0.5;",
    "  vec2 u = mod(p, s) - h, v = mod(p - h, s) - h;",
    "  return dot(u, u) < dot(v, v) ? p - u : p - v;",
    "}",

    // Spikes are pushed out of the liquid's own surface, not placed on top of it:
    // height is measured from the real surface (the body distance), so the patch
    // follows every bend and neck, and each spike rises along the local normal.
    // The hex grid lives on the tangent plane at the touch point; within a cell the
    // height falls to zero before the cell edge, so neighbouring cells never clash.
    "const float SP = 0.064;", // spike spacing
    "const float RB = 0.029;", // spike base radius (< SP / 2)
    "float map(vec3 p) {",
    "  float b = body(p);",
    "  if (uS < 0.01) return b;",
    "  vec3 q = p - uP;",
    "  float lq2 = dot(q, q);",
    "  if (lq2 > 0.3) return b;",
    "  vec2 tp = vec2(dot(q, T1), dot(q, T2));",
    "  float l = length(tp - hexCell(tp, SP));",
    // tallest at the touch point, fading out; nothing on the far side of thin drops
    "  float H = 0.2 * uS * exp(-lq2 / 0.045) * smoothstep(-0.28, -0.12, dot(q, uN));",
    "  float x = clamp(1.0 - l / RB, 0.0, 1.0);",
    "  float d = b - H * x * sqrt(x);", // slightly concave flanks, needle-sharp tip
    // divide by the steepest slope so the march never steps through a spike
    "  return d / (1.0 + 1.5 * H / RB);",
    "}",

    "vec3 normal(vec3 p) {",
    "  const vec2 e = vec2(0.001, -0.001);",
    "  return normalize(e.xyy * map(p + e.xyy) + e.yyx * map(p + e.yyx) + e.yxy * map(p + e.yxy) + e.xxx * map(p + e.xxx));",
    "}",

    // studio surroundings reflected by the liquid: softboxes, a key light, a rim
    "vec3 env(vec3 r) {",
    "  vec3 c = vec3(0.006) + vec3(0.07) * smoothstep(0.0, 1.0, r.y);",
    "  c += vec3(2.2) * smoothstep(0.9, 0.95, 0.5 + 0.5 * sin(r.x * 2.4 + 1.4)) * smoothstep(0.0, 0.5, r.y);",
    "  c += vec3(1.2) * smoothstep(0.93, 0.97, 0.5 + 0.5 * sin(r.y * 3.0 - 0.6)) * smoothstep(0.1, 0.7, -r.x);",
    "  c += vec3(0.5) * smoothstep(0.94, 0.98, 0.5 + 0.5 * sin(r.x * 5.0 - r.y * 2.0));",
    "  c += vec3(1.6) * pow(max(dot(r, normalize(vec3(-0.5, 0.8, 0.45))), 0.0), 30.0);",
    "  c += vec3(0.35) * pow(max(dot(r, normalize(vec3(0.8, -0.3, 0.5))), 0.0), 5.0);",
    "  return c;",
    "}",

    "void main() {",
    // narrow (portrait) screens pull the camera back so the liquid fits the width
    "  float zoom = max(1.0, 0.85 * uRes.y / uRes.x);",
    "  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y * zoom;",
    "  T1 = normalize(abs(uN.y) < 0.9 ? cross(uN, vec3(0.0, 1.0, 0.0)) : cross(uN, vec3(1.0, 0.0, 0.0)));",
    "  T2 = cross(uN, T1);",
    "  vec3 ro = vec3(0.0, 0.0, 5.0);",
    "  vec3 rd = normalize(vec3(uv, -1.6));",
    "  vec2 vu = uv / zoom;",
    "  vec3 col = vec3(0.035, 0.039, 0.035) * (1.0 - 0.35 * dot(vu, vu));",
    // bounding sphere: skip the march for pixels that can never hit the liquid
    "  vec3 oc = ro - C;",
    "  float b = dot(oc, rd);",
    "  float h = b * b - dot(oc, oc) + 1.7 * 1.7;",
    "  if (h > 0.0) {",
    "    h = sqrt(h);",
    "    float t = max(-b - h, 0.0), tf = -b + h;",
    "    bool hit = false, escaped = false;",
    "    float dist = 1.0;",
    "    for (int i = 0; i < 150; i++) {",
    "      dist = map(ro + rd * t);",
    "      if (dist < 0.0008) { hit = true; break; }",
    "      t += dist * 0.9;",
    "      if (t > tf) { escaped = true; break; }",
    "    }",
    // rays that run out of steps right next to a spike tip still count as a hit
    "    if (!hit && !escaped && dist < 0.01) hit = true;",
    "    if (hit) {",
    "      vec3 p = ro + rd * t;",
    "      vec3 n = normal(p);",
    "      vec3 r = reflect(rd, n);",
    "      float fres = pow(1.0 - max(dot(n, -rd), 0.0), 3.0);",
    "      float ao = clamp(map(p + n * 0.08) / 0.08, 0.35, 1.0);",
    "      col = env(r) * (0.45 + 0.55 * fres) * ao + vec3(0.006);",
    "      col = col / (1.0 + col * 0.8) * 1.2;",
    "    }",
    "  }",
    // a whisper of noise so the dark gradient does not band into rings
    "  col += (fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) / 255.0;",
    "  gl_FragColor = vec4(col, 1.0);",
    "}"
  ].join("\n");

  /* the same body in JS, to find where the pointer ray meets the liquid */
  function smin(a, b, k) {
    var h = Math.min(Math.max(0.5 + 0.5 * (b - a) / k, 0), 1);
    return b + (a - b) * h - k * h * (1 - h);
  }
  function body(x, y, z, t) {
    var d = Math.hypot(x, y - CY, z) - R0;
    for (var f = 0; f < LOBES; f++) {
      var ox = Math.sin(t * (0.31 + 0.07 * f) + f * 1.7) * 0.85;
      var oy = CY + Math.cos(t * (0.27 + 0.05 * f) + f * 2.3) * 0.45;
      var oz = Math.sin(t * (0.23 + 0.06 * f) + f) * 0.4;
      d = smin(d, Math.hypot(x - ox, y - oy, z - oz) - (0.2 + 0.05 * Math.sin(f * 3.1 + t * 0.5)), K);
    }
    return d;
  }
  function touch(ux, uy, t) { // ux, uy: shader-space uv of the pointer
    var len = Math.hypot(ux, uy, 1.6), dx = ux / len, dy = uy / len, dz = -1.6 / len;
    var s = 3.2;
    for (var i = 0; i < 70 && s < 7; i++) {
      var x = dx * s, y = dy * s, z = 5 + dz * s, d = body(x, y, z, t);
      if (d < 0.002) {
        var e = 0.002;
        var nx = body(x + e, y, z, t) - body(x - e, y, z, t);
        var ny = body(x, y + e, z, t) - body(x, y - e, z, t);
        var nz = body(x, y, z + e, t) - body(x, y, z - e, t);
        var nl = Math.hypot(nx, ny, nz) || 1;
        return { x: x, y: y, z: z, nx: nx / nl, ny: ny / nl, nz: nz / nl };
      }
      s += d * 0.9;
    }
    return null;
  }

  // keep the spike patch stuck to the liquid as it flows: slide it back onto the surface
  function snap(sp, t) {
    for (var i = 0; i < 3; i++) {
      var d = body(sp.x, sp.y, sp.z, t);
      sp.x -= sp.nx * d; sp.y -= sp.ny * d; sp.z -= sp.nz * d;
    }
    var e = 0.002, x = sp.x, y = sp.y, z = sp.z;
    var nx = body(x + e, y, z, t) - body(x - e, y, z, t);
    var ny = body(x, y + e, z, t) - body(x, y - e, z, t);
    var nz = body(x, y, z + e, t) - body(x, y, z - e, t);
    var nl = Math.hypot(nx, ny, nz) || 1;
    sp.nx = nx / nl; sp.ny = ny / nl; sp.nz = nz / nl;
  }

  function shader(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.warn(gl.getShaderInfoLog(s)); return null; }
    return s;
  }
  var vs = shader(gl.VERTEX_SHADER, VERT), fs = shader(gl.FRAGMENT_SHADER, FRAG);
  if (!vs || !fs) { canvas.remove(); return; }
  var prog = gl.createProgram();
  gl.attachShader(prog, vs);
  gl.attachShader(prog, fs);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { canvas.remove(); return; }
  gl.useProgram(prog);

  // one triangle that covers the screen
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(prog, "a");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  var U = {};
  ["uRes", "uTime", "uP", "uN", "uS"].forEach(function (n) { U[n] = gl.getUniformLocation(prog, n); });

  /* Render below native resolution: the surface is smooth, so upscaling is
     invisible and it keeps phones cool. */
  function resize() {
    var scale = window.innerWidth <= 720 ? 0.55 : 0.75;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = Math.max(1, Math.round(canvas.clientWidth * dpr * scale));
    var h = Math.max(1, Math.round(canvas.clientHeight * dpr * scale));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
  }

  // pointer in shader uv space, or null when it is off the hero
  var pointer = null;
  function onPointer(e) {
    var r = canvas.getBoundingClientRect();
    if (e.clientY < r.top || e.clientY > r.bottom || e.clientX < r.left || e.clientX > r.right) { pointer = null; return; }
    var zoom = Math.max(1, 0.85 * r.height / r.width);
    pointer = {
      x: (e.clientX - r.left - r.width / 2) / r.height * zoom,
      y: -(e.clientY - r.top - r.height / 2) / r.height * zoom
    };
  }
  window.addEventListener("pointermove", onPointer, { passive: true });
  window.addEventListener("pointerdown", onPointer, { passive: true });
  window.addEventListener("pointerup", function (e) { if (e.pointerType !== "mouse") pointer = null; });
  window.addEventListener("pointercancel", function () { pointer = null; });
  document.addEventListener("pointerleave", function () { pointer = null; });

  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var start = performance.now(), running = false, visible = true, raf = 0;
  var spot = { x: 0, y: CY, z: R0, nx: 0, ny: 0, nz: 1, s: 0 };

  function frame(now) {
    raf = 0;
    resize();
    var t = reduced ? 12 : (now - start) / 1000;
    var hit = pointer && touch(pointer.x, pointer.y, t);
    if (hit) {
      // first touch snaps the patch into place; after that it glides with the pointer
      var a = spot.s < 0.05 ? 1 : 0.25;
      spot.x += (hit.x - spot.x) * a; spot.y += (hit.y - spot.y) * a; spot.z += (hit.z - spot.z) * a;
      spot.nx += (hit.nx - spot.nx) * a; spot.ny += (hit.ny - spot.ny) * a; spot.nz += (hit.nz - spot.nz) * a;
      var nl = Math.hypot(spot.nx, spot.ny, spot.nz) || 1;
      spot.nx /= nl; spot.ny /= nl; spot.nz /= nl;
    }
    if (spot.s > 0.01) snap(spot, t);
    // spikes rise slowly (low sensitivity) and sink back a little quicker
    spot.s += ((hit ? 1 : 0) - spot.s) * (hit ? 0.035 : 0.05);
    gl.uniform2f(U.uRes, canvas.width, canvas.height);
    gl.uniform1f(U.uTime, t);
    gl.uniform3f(U.uP, spot.x, spot.y, spot.z);
    gl.uniform3f(U.uN, spot.nx, spot.ny, spot.nz);
    gl.uniform1f(U.uS, spot.s);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    if (running && !reduced) raf = requestAnimationFrame(frame);
  }
  function update() {
    var should = visible && !document.hidden;
    if (should && !running) { running = true; if (!raf) raf = requestAnimationFrame(frame); }
    else if (!should) { running = false; if (raf) { cancelAnimationFrame(raf); raf = 0; } }
  }
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { visible = es[0].isIntersecting; update(); }).observe(canvas);
  }
  document.addEventListener("visibilitychange", update);
  window.addEventListener("resize", function () { if (reduced) requestAnimationFrame(frame); });
  canvas.addEventListener("webglcontextlost", function (e) { e.preventDefault(); running = false; });
  update();
})();
