import { useEffect, useRef } from "react";

interface LifecycleAnimationProps {
  onFlyStart?: () => void;
  onComplete?: () => void;
}

export default function LifecycleAnimation({ onFlyStart, onComplete }: LifecycleAnimationProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const q = <T extends Element = Element>(sel: string): T =>
      root.querySelector(sel) as T;
    const qa = <T extends Element = Element>(sel: string): T[] =>
      Array.from(root.querySelectorAll(sel)) as T[];

    const svg = q<SVGSVGElement>("#life");
    if (!svg) return;

    const scene = q<SVGGElement>("#scene");
    const stageElements = q<SVGGElement>("#stage-elements");
    const dots = qa<SVGGElement>("#dots .dot");
    const bodies = dots.map(
      (g) => g.querySelector(".bd") as SVGCircleElement,
    );
    const track = q<SVGLineElement>("#track");
    const packetG = q<SVGGElement>("#packetG");
    const ghost1 = q<SVGGElement>("#ghost1");
    const ghost2 = q<SVGGElement>("#ghost2");
    const gauge = q<SVGCircleElement>("#gauge");
    const delta = q<SVGCircleElement>("#delta");
    const head = q<SVGCircleElement>("#head");
    const guide = q<SVGCircleElement>("#ring-guide");
    const pulse1 = q<SVGCircleElement>("#edit-pulse");
    const sweep = q<SVGCircleElement>("#sweep");
    const score = q<SVGTextElement>("#score");
    const phaseWord = q<HTMLDivElement>("#phaseWord");
    const phaseLine = q<HTMLDivElement>("#phaseLine");

    if (
      !scene ||
      !stageElements ||
      dots.length !== 5 ||
      bodies.some((b) => !b) ||
      !track ||
      !packetG ||
      !ghost1 ||
      !ghost2 ||
      !gauge ||
      !delta ||
      !head ||
      !guide ||
      !pulse1 ||
      !sweep ||
      !score ||
      !phaseWord ||
      !phaseLine
    ) {
      return;
    }

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let cleanupTimer: number | null = null;

    /* ---------- tuning ---------- */
    const DUR = 18.2;
    const CX = 410;
    const CY = 210;
    const R = 172;
    const ROW_Y = 205;
    const BASE = 0.74;
    const TARGET = 0.94;

    interface TimingMap {
      trackIn: number;
      execStart: number;
      moveStart: number;
      moveEnd: number;
      execEnd: number;
      morphStart: number;
      morphDur: number;
      morphStag: number;
      evalStart: number;
      evalEnd: number;
      rerunStart: number;
      rerunEnd: number;
      deltaStart: number;
      deltaEnd: number;
      compStart: number;
      compEnd: number;
      shimmer: number;
      holdEnd: number;
      fadeEnd: number;
    }

    const T: TimingMap = {
      trackIn: 3.35,
      execStart: 3.7,
      moveStart: 3.95,
      moveEnd: 6.7,
      execEnd: 7.0,
      morphStart: 7.0,
      morphDur: 1.2,
      morphStag: 0.06,
      evalStart: 8.55,
      evalEnd: 10.55,
      rerunStart: 10.75,
      rerunEnd: 12.0,
      deltaStart: 12.1,
      deltaEnd: 15.1,
      compStart: 15.25,
      compEnd: 16.6,
      shimmer: 16.5,
      holdEnd: 17.5,
      fadeEnd: 18.2,
    };

    /* ---------- helpers ---------- */
    function clamp(v: number, a: number, b: number): number {
      return v < a ? a : v > b ? b : v;
    }
    function lerp(a: number, b: number, t: number): number {
      return a + (b - a) * t;
    }
    function seg(t: number, a: number, b: number): number {
      return clamp((t - a) / (b - a), 0, 1);
    }

    function bezier(x1: number, y1: number, x2: number, y2: number) {
      const cx = 3 * x1;
      const bx = 3 * (x2 - x1) - cx;
      const ax = 1 - cx - bx;
      const cy = 3 * y1;
      const by = 3 * (y2 - y1) - cy;
      const ay = 1 - cy - by;
      const X = (t: number) => ((ax * t + bx) * t + cx) * t;
      const Y = (t: number) => ((ay * t + by) * t + cy) * t;
      const dX = (t: number) => (3 * ax * t + 2 * bx) * t + cx;
      return (x: number) => {
        if (x <= 0) return 0;
        if (x >= 1) return 1;
        let t = x;
        for (let i = 0; i < 6; i++) {
          const err = X(t) - x;
          const d = dX(t);
          if (d < 1e-4) break;
          t = Math.min(1, Math.max(0, t - err / d));
        }
        if (Math.abs(X(t) - x) > 1e-4) {
          let lo = 0;
          let hi = 1;
          t = x;
          for (let i = 0; i < 24; i++) {
            if (X(t) < x) lo = t;
            else hi = t;
            t = (lo + hi) / 2;
          }
        }
        return Y(t);
      };
    }

    const OUT = bezier(0.23, 1, 0.32, 1);
    const INOUT = bezier(0.77, 0, 0.175, 1);

    function qb(p0: number, p1: number, p2: number, e: number): number {
      const u = 1 - e;
      return u * u * p0 + 2 * u * e * p1 + e * e * p2;
    }

    function rowPos(i: number): { x: number; y: number } {
      return { x: 410 + (i - 2) * 105, y: ROW_Y };
    }
    function circPos(i: number): { x: number; y: number } {
      const a = ((-90 + i * 72) * Math.PI) / 180;
      return { x: CX + R * Math.cos(a), y: CY + R * Math.sin(a) };
    }
    function dotColor(a: number): string {
      return (
        "rgb(" +
        Math.round(lerp(213, 19, a)) +
        "," +
        Math.round(lerp(211, 13, a)) +
        "," +
        Math.round(lerp(249, 221, a)) +
        ")"
      );
    }

    /* ---------- per-loop state ---------- */
    const pulses: { dot: number; t0: number; dur: number; amp: number }[] = [];
    const act = [-1, -1, -1, -1, -1];
    const settled = [false, false, false, false, false];
    const scanned = [false, false, false, false, false];
    const rerun = [false, false, false, false, false];
    let shimmered = false;
    let prevPx = 88;
    let lastKey: string | null = "Assemble|The steps come together into one kit";

    function pulse(i: number, t0: number, dur: number, amp: number): void {
      pulses.push({ dot: i, t0, dur, amp });
    }
    function pulseScale(i: number, t: number): number {
      let s = 1;
      for (let k = 0; k < pulses.length; k++) {
        const p = pulses[k];
        if (p.dot !== i) continue;
        const u = (t - p.t0) / p.dur;
        if (u > 0 && u < 1) s += p.amp * Math.sin(u * Math.PI);
      }
      return s;
    }

    /* ---------- captions ---------- */
    function setCaption(word: string, line: string): void {
      const key = word + "|" + line;
      if (key === lastKey) return;
      lastKey = key;
      const out: Keyframe[] = [
        { opacity: 1, transform: "translateY(0px)", filter: "blur(0px)" },
        { opacity: 0, transform: "translateY(-5px)", filter: "blur(2px)" },
      ];
      phaseWord.animate(out, { duration: 130, easing: "ease-in", fill: "forwards" });
      phaseLine.animate(out, { duration: 130, easing: "ease-in", fill: "forwards" });
      setTimeout(() => {
        if (lastKey !== key) return;
        phaseWord.textContent = word || "\u00A0";
        phaseLine.textContent = line || "\u00A0";
        if (!word && !line) return;
        const inn: Keyframe[] = [
          { opacity: 0, transform: "translateY(6px)", filter: "blur(2px)" },
          { opacity: 1, transform: "translateY(0px)", filter: "blur(0px)" },
        ];
        const ease = "cubic-bezier(0.23,1,0.32,1)";
        phaseWord.animate(inn, { duration: 260, easing: ease, fill: "forwards" });
        phaseLine.animate(inn, { duration: 260, easing: ease, fill: "forwards" });
      }, 135);
    }

    const phases = [
      { t: 0, name: "Assemble", line: "The steps come together into one kit" },
      { t: T.execStart, name: "Execute", line: "A document flows through each step" },
      { t: T.evalStart, name: "Evaluate", line: "A judge model scores the output out of 100" },
      { t: T.rerunStart, name: "Improve", line: "A better kit, a better answer" },
      { t: T.compStart, name: "Complete", line: "Every step proven, end to end" },
      { t: T.holdEnd, name: "", line: "" },
    ];
    function phaseAt(t: number): { name: string; line: string } {
      for (let i = phases.length - 1; i >= 0; i--) {
        if (t >= phases[i].t) return phases[i];
      }
      return phases[0];
    }

    /* ---------- assemble ---------- */
    const ASM_DUR = 1.45;
    function asmStart(i: number): number {
      return 0.15 + i * 0.22;
    }
    function asmState(
      i: number,
      t: number,
    ): { x: number; y: number; sc: number; o: number } {
      const u = (t - asmStart(i)) / ASM_DUR;
      const rp = rowPos(i);
      if (u <= 0) return { x: 410, y: 440, sc: 0.35, o: 0 };
      if (u >= 1) {
        if (!settled[i]) {
          settled[i] = true;
          pulse(i, t, 0.35, 0.05);
        }
        return { x: rp.x, y: rp.y, sc: 1, o: 1 };
      }
      const dip = seg(u, 0, 0.12);
      const rise = seg(u, 0.12, 1);
      const o = seg(u, 0, 0.14);
      if (rise <= 0) {
        const dy = INOUT(dip);
        return { x: 410, y: 440 + 5 * dy, sc: lerp(0.35, 0.42, dy), o };
      }
      const e = OUT(rise);
      const p1x = (410 + rp.x) / 2 + (i - 2) * 22;
      const p1y = (445 + rp.y) / 2 - 24;
      return {
        x: qb(410, p1x, rp.x, e),
        y: qb(445, p1y, rp.y, e),
        sc: lerp(0.42, 1, e),
        o,
      };
    }

    /* ---------- frame ---------- */
    function frame(t: number, dt: number): void {
      let i: number;

      // execute
      const moveU = seg(t, T.moveStart, T.moveEnd);
      const px = lerp(88, 732, INOUT(moveU));
      const v = dt > 0 ? (px - prevPx) / dt : 0;
      prevPx = px;
      const speedN = clamp(Math.abs(v) / 340, 0, 1);
      const packO =
        seg(t, T.execStart, T.execStart + 0.3) *
        (1 - seg(t, T.moveEnd - 0.05, T.execEnd));
      const packS =
        lerp(0.8, 1, OUT(seg(t, T.execStart, T.execStart + 0.35))) *
        (1 - 0.15 * seg(t, T.moveEnd - 0.05, T.execEnd));
      const sqx = 1 + 0.1 * speedN;
      const sqy = 1 - 0.06 * speedN;
      packetG.style.transform =
        "translate(" +
        px.toFixed(1) +
        "px," +
        ROW_Y +
        "px) scale(" +
        (packS * sqx).toFixed(3) +
        "," +
        (packS * sqy).toFixed(3) +
        ")";
      packetG.style.opacity = packO.toFixed(3);
      ghost1.style.transform =
        "translate(" +
        (px - v * 0.055).toFixed(1) +
        "px," +
        ROW_Y +
        "px) scale(" +
        sqx.toFixed(3) +
        "," +
        sqy.toFixed(3) +
        ")";
      ghost2.style.transform =
        "translate(" +
        (px - v * 0.11).toFixed(1) +
        "px," +
        ROW_Y +
        "px) scale(" +
        sqx.toFixed(3) +
        "," +
        sqy.toFixed(3) +
        ")";
      ghost1.style.opacity = (0.2 * speedN * packO).toFixed(3);
      ghost2.style.opacity = (0.1 * speedN * packO).toFixed(3);
      track.style.opacity = (
        0.9 *
        seg(t, T.trackIn, T.trackIn + 0.35) *
        (1 - seg(t, T.morphStart, T.morphStart + 0.4))
      ).toFixed(3);

      // gauge
      const gaugeIn = seg(t, T.morphStart + 0.15, T.morphStart + 0.85);
      const fr = OUT(seg(t, T.evalStart, T.evalEnd)) * BASE;
      const dfr = OUT(seg(t, T.deltaStart, T.deltaEnd)) * (TARGET - BASE);
      const frac = fr + dfr;
      gauge.style.opacity = (0.9 * gaugeIn).toFixed(3);
      gauge.style.strokeDashoffset = (100 * (1 - fr)).toFixed(2);
      delta.style.opacity = (0.9 * gaugeIn).toFixed(3);
      delta.style.strokeDashoffset = (100 * (1 - dfr)).toFixed(2);
      guide.style.opacity = (0.5 * gaugeIn).toFixed(3);

      // completion
      const comp = INOUT(seg(t, T.compStart, T.compEnd));
      sweep.style.strokeDashoffset = (100 * (1 + comp * TARGET)).toFixed(2);
      sweep.style.opacity = (
        0.9 *
        seg(t, T.compStart, T.compStart + 0.15) *
        gaugeIn
      ).toFixed(3);

      // score
      score.textContent = Math.round(frac * 100).toString();
      score.style.opacity = seg(t, T.evalStart - 0.1, T.evalStart + 0.25).toFixed(3);
      const sa = seg(t, T.deltaStart, T.deltaEnd);
      score.setAttribute(
        "fill",
        "rgb(" +
          Math.round(lerp(17, 19, sa)) +
          "," +
          Math.round(lerp(20, 13, sa)) +
          "," +
          Math.round(lerp(24, 221, sa)) +
          ")",
      );

      // head
      const ha = ((-90 + frac * 360) * Math.PI) / 180;
      head.setAttribute(
        "transform",
        "translate(" +
          (CX + R * Math.cos(ha)).toFixed(1) +
          " " +
          (CY + R * Math.sin(ha)).toFixed(1) +
          ")",
      );
      head.style.opacity = (gaugeIn * (frac > 0.005 ? 1 : 0)).toFixed(3);
      head.setAttribute("stroke", dfr > 0 ? "#130DDD" : "#716EEB");

      // improve
      const orU = seg(t, T.rerunStart, T.rerunEnd);
      if (orU > 0 && orU < 1) {
        const orE = INOUT(orU);
        const orA = ((-90 + orE * 360) * Math.PI) / 180;
        const oDeg = orE * 360;
        packetG.style.transform =
          "translate(" +
          (CX + R * Math.cos(orA)).toFixed(1) +
          "px," +
          (CY + R * Math.sin(orA)).toFixed(1) +
          "px) rotate(" +
          oDeg.toFixed(1) +
          "deg) scale(1.08,0.92)";
        packetG.style.opacity = (
          seg(t, T.rerunStart, T.rerunStart + 0.15) *
          (1 - seg(t, T.rerunEnd - 0.15, T.rerunEnd))
        ).toFixed(3);
        const tl = Math.min(orE, 0.16) * 100;
        pulse1.style.strokeDasharray = tl.toFixed(1) + " 200";
        pulse1.style.strokeDashoffset = (-(orE * 100 - tl)).toFixed(1);
        pulse1.style.opacity = (
          0.85 *
          (1 - seg(t, T.rerunEnd - 0.2, T.rerunEnd))
        ).toFixed(3);
        for (i = 0; i < 5; i++) {
          if (!rerun[i] && orE >= i / 5 + 0.01) {
            rerun[i] = true;
            pulse(i, t, 0.4, 0.14);
          }
        }
      } else {
        pulse1.style.opacity = "0";
      }

      // judge scans
      for (i = 0; i < 5; i++) {
        if (!scanned[i] && frac >= i / 5 + 0.02) {
          scanned[i] = true;
          pulse(i, t, 0.4, 0.12);
        }
      }
      if (!shimmered && t >= T.shimmer) {
        shimmered = true;
        for (i = 0; i < 5; i++) pulse(i, T.shimmer + i * 0.06, 0.35, 0.07);
      }

      // dots
      for (i = 0; i < 5; i++) {
        const a = asmState(i, t);
        const m = INOUT(
          seg(
            t,
            T.morphStart + i * T.morphStag,
            T.morphStart + i * T.morphStag + T.morphDur,
          ),
        );
        let x: number;
        let y: number;
        let sc: number;
        if (m > 0) {
          const cp = circPos(i);
          x = lerp(a.x, cp.x, m);
          y = lerp(a.y, cp.y, m);
          sc = lerp(a.sc, 26 / 30, m);
        } else {
          x = a.x;
          y = a.y;
          sc = a.sc;
        }
        if (act[i] < 0 && moveU > 0 && px >= rowPos(i).x - 12) {
          act[i] = t;
          pulse(i, t, 0.45, 0.18);
        }
        let lit = act[i] >= 0 ? seg(t, act[i], act[i] + 0.35) : 0;
        if (m >= 1) lit = 1;
        sc *= pulseScale(i, t);
        const g = dots[i];
        g.style.transform =
          "translate(" +
          x.toFixed(1) +
          "px," +
          y.toFixed(1) +
          "px) scale(" +
          sc.toFixed(3) +
          ")";
        g.style.opacity = a.o.toFixed(3);
        bodies[i].setAttribute("fill", dotColor(lit));
      }

      stageElements.style.opacity = (1 - seg(t, T.holdEnd, T.fadeEnd)).toFixed(3);

      const ph = phaseAt(t);
      setCaption(ph.name, ph.line);
    }

    /* ---------- reduced motion static state ---------- */
    if (reduce) {
      for (let i = 0; i < 5; i++) {
        const cp = circPos(i);
        dots[i].style.transform =
          "translate(" +
          cp.x.toFixed(1) +
          "px," +
          cp.y.toFixed(1) +
          "px) scale(" +
          (26 / 30).toFixed(3) +
          ")";
        dots[i].style.opacity = "1";
        bodies[i].setAttribute("fill", "#130DDD");
      }
      guide.style.opacity = "0.5";
      gauge.style.opacity = "0.9";
      gauge.style.strokeDashoffset = (100 * (1 - BASE)).toFixed(2);
      delta.style.opacity = "0.9";
      delta.style.strokeDashoffset = (100 * (1 - (TARGET - BASE))).toFixed(2);
      sweep.style.opacity = "0.9";
      sweep.style.strokeDashoffset = (100 * (1 + TARGET)).toFixed(2);
      const fa = ((-90 + TARGET * 360) * Math.PI) / 180;
      head.setAttribute(
        "transform",
        "translate(" +
          (CX + R * Math.cos(fa)).toFixed(1) +
          " " +
          (CY + R * Math.sin(fa)).toFixed(1) +
          ")",
      );
      head.style.opacity = "1";
      head.setAttribute("stroke", "#130DDD");
      score.textContent = Math.round(TARGET * 100).toString();
      score.style.opacity = "1";
      score.setAttribute("fill", "#130DDD");
      phaseWord.textContent = "Assemble";
      phaseLine.textContent = "Execute · Evaluate · Improve · Complete";
      cleanupTimer = window.setTimeout(() => flyToLogo(), 2500);
      return;
    }

    /* ---------- fly the five dots to the nav logo ---------- */
    function flyToLogo() {
      onFlyStart?.();

      const logo = document.getElementById("clerk-logo");
      const logoDots = logo
        ? Array.from(logo.querySelectorAll(".clerk-dot"))
        : [];
      if (logoDots.length !== 5) {
        onComplete?.();
        return;
      }

      const svgRect = svg.getBoundingClientRect();
      const unitX = 820 / svgRect.width;

      // Hide the remaining stage elements so only the dots fly
      stageElements.style.opacity = "0";
      score.style.opacity = "0";
      head.style.opacity = "0";
      guide.style.opacity = "0";
      sweep.style.opacity = "0";
      gauge.style.opacity = "0";
      delta.style.opacity = "0";
      pulse1.style.opacity = "0";
      track.style.opacity = "0";
      packetG.style.opacity = "0";
      ghost1.style.opacity = "0";
      ghost2.style.opacity = "0";
      svg.style.overflow = "visible";

      const targets = logoDots.map((ld) => {
        const r = ld.getBoundingClientRect();
        const targetCx = (r.left + r.width / 2 - svgRect.left) * unitX;
        const targetCy = (r.top + r.height / 2 - svgRect.top) * unitX;
        const targetScale = (r.width / 2) / (26 / unitX);
        return { x: targetCx, y: targetCy, scale: targetScale };
      });

      dots.forEach((dot, i) => {
        const cp = circPos(i);
        const target = targets[i];
        dot.style.opacity = "1";
        dot.animate(
          [
            {
              transform: `translate(${cp.x.toFixed(1)}px, ${cp.y.toFixed(1)}px) scale(0.867)`,
            },
            {
              transform: `translate(${target.x.toFixed(1)}px, ${target.y.toFixed(1)}px) scale(${target.scale.toFixed(3)})`,
            },
          ],
          {
            duration: 900,
            easing: "cubic-bezier(0.77, 0, 0.175, 1)",
            fill: "forwards",
          },
        );
      });

      cleanupTimer = window.setTimeout(() => {
        onComplete?.();
      }, 900);
    }

    /* ---------- loop driver: play once on load ---------- */
    let running = false;
    let raf: number | null = null;
    let acc = 0;
    let last = 0;
    let done = false;

    function tick(ts: number): void {
      if (!running || done) return;
      if (!last) last = ts;
      const dt = Math.min((ts - last) / 1000, 0.05);
      last = ts;
      acc += dt;
      const t = Math.min(acc, DUR);
      frame(t, dt);
      if (acc >= DUR) {
        done = true;
        stop();
        flyToLogo();
        return;
      }
      raf = requestAnimationFrame(tick);
    }
    function start(): void {
      if (running) return;
      running = true;
      last = 0;
      raf = requestAnimationFrame(tick);
    }
    function stop(): void {
      running = false;
      if (raf) cancelAnimationFrame(raf);
      raf = null;
    }

    start();

    return () => {
      stop();
      if (cleanupTimer) window.clearTimeout(cleanupTimer);
    };
  }, [onComplete, onFlyStart]);

  return (
    <div ref={rootRef} className="stage">
      <svg
        id="life"
        viewBox="0 0 820 460"
        role="img"
        aria-label="Animated loop showing a reasoning kit assembling from five dots into a row, executing by passing a document through each step, moving into a gauge that is scored, and improving from 74 to 94."
      >
        <g id="scene">
          <g id="stage-elements">
            <line
              id="track"
              x1="70"
              y1="205"
              x2="750"
              y2="205"
              stroke="#E4E3FB"
              strokeWidth="3"
              strokeLinecap="round"
            />
            <circle id="ring-guide" cx="410" cy="210" r="172" />
            <circle
              id="gauge"
              cx="410"
              cy="210"
              r="172"
              pathLength="100"
              stroke="#716EEB"
              strokeDasharray="100 100"
              strokeDashoffset="100"
            />
            <circle
              id="delta"
              cx="410"
              cy="210"
              r="172"
              pathLength="100"
              strokeDasharray="100 100"
              strokeDashoffset="100"
            />
            <circle id="edit-pulse" cx="410" cy="210" r="172" pathLength="100" />
            <circle
              id="sweep"
              cx="410"
              cy="210"
              r="172"
              pathLength="100"
              stroke="#130DDD"
              strokeDasharray="100 100"
              strokeDashoffset="100"
            />
            <text id="score" x="410" y="246" fill="#111418">
              94
            </text>
            <g id="ghost2">
              <rect x="-15" y="-11" width="30" height="22" rx="6" />
            </g>
            <g id="ghost1">
              <rect x="-15" y="-11" width="30" height="22" rx="6" />
            </g>
            <g id="packetG">
              <rect id="packet" x="-15" y="-11" width="30" height="22" rx="6" />
            </g>
            <circle id="head" r="5.5" stroke="#716EEB" strokeWidth="3" />
          </g>
          <g id="dots">
            <g className="dot">
              <circle className="sh" cy="5" r="29" />
              <circle className="bd" r="30" fill="#D5D3F9" />
            </g>
            <g className="dot">
              <circle className="sh" cy="5" r="29" />
              <circle className="bd" r="30" fill="#D5D3F9" />
            </g>
            <g className="dot">
              <circle className="sh" cy="5" r="29" />
              <circle className="bd" r="30" fill="#D5D3F9" />
            </g>
            <g className="dot">
              <circle className="sh" cy="5" r="29" />
              <circle className="bd" r="30" fill="#D5D3F9" />
            </g>
            <g className="dot">
              <circle className="sh" cy="5" r="29" />
              <circle className="bd" r="30" fill="#D5D3F9" />
            </g>
          </g>
        </g>
      </svg>
      <noscript>
        <style>
          {`
            #ring-guide{opacity:.5}
            #gauge{opacity:.9;stroke-dashoffset:26}
            #delta{opacity:.9;stroke-dashoffset:80}
            #sweep{opacity:.9;stroke-dashoffset:194}
            #head{opacity:1;stroke:#130DDD;transform:translate(346.7px,50.1px)}
            #score{opacity:1;fill:#130DDD}
            #dots .dot{opacity:1}
            #dots .dot:nth-child(1){transform:translate(410px,38px) scale(.867)}
            #dots .dot:nth-child(2){transform:translate(573.6px,156.9px) scale(.867)}
            #dots .dot:nth-child(3){transform:translate(511.1px,349.1px) scale(.867)}
            #dots .dot:nth-child(4){transform:translate(308.9px,349.1px) scale(.867)}
            #dots .dot:nth-child(5){transform:translate(246.4px,156.9px) scale(.867)}
            #dots .bd{fill:#130DDD}
          `}
        </style>
      </noscript>
      <div className="phase">
        <div id="phaseWord">Assemble</div>
        <div id="phaseLine">The steps come together into one kit</div>
      </div>
    </div>
  );
}
