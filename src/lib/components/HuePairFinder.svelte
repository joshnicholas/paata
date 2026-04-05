<script>
	let { colour = '#ffffff' } = $props();
	let bgManual = $state(null); // null = track colour picker
	let fgInput = $state('#ff6600');

	const bgInput = $derived(bgManual ?? colour);
	let level = $state('aa');
	let mode = $state('fg'); // 'fg' | 'bg-edge'

	// ── OKLCH ────────────────────────────────────────────────────────────────

	function sRGBToLinear(c) { return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; }
	function linearToSRGB(c) { return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; }

	function hexToOklch(hex) {
		let r=parseInt(hex.slice(1,3),16)/255, g=parseInt(hex.slice(3,5),16)/255, b=parseInt(hex.slice(5,7),16)/255;
		r=sRGBToLinear(r); g=sRGBToLinear(g); b=sRGBToLinear(b);
		const l=Math.cbrt(0.4122214708*r+0.5363325363*g+0.0514459929*b);
		const m=Math.cbrt(0.2119034982*r+0.6806995451*g+0.1073969566*b);
		const s=Math.cbrt(0.0883024619*r+0.2817188376*g+0.6299787005*b);
		const L=0.2104542553*l+0.7936177850*m-0.0040720468*s;
		const a=1.9779984951*l-2.4285922050*m+0.4505937099*s;
		const bv=0.0259040371*l+0.7827717662*m-0.8086757660*s;
		return { L, C:Math.sqrt(a*a+bv*bv), H:(Math.atan2(bv,a)*180/Math.PI+360)%360 };
	}

	function oklchToHex(L, C, H) {
		const h=H*Math.PI/180, a=C*Math.cos(h), bv=C*Math.sin(h);
		const l_=L+0.3963377774*a+0.2158037573*bv;
		const m_=L-0.1055613458*a-0.0638541728*bv;
		const s_=L-0.0894841775*a-1.2914855480*bv;
		const lr=l_**3, mr=m_**3, sr=s_**3;
		const r=linearToSRGB(4.0767416621*lr-3.3077115913*mr+0.2309699292*sr);
		const g=linearToSRGB(-1.2684380046*lr+2.6097574011*mr-0.3413193965*sr);
		const b=linearToSRGB(-0.0041960863*lr-0.7034186147*mr+1.6076135661*sr);
		const clamp=v=>Math.round(Math.min(1,Math.max(0,v))*255);
		return '#'+[clamp(r),clamp(g),clamp(b)].map(v=>v.toString(16).padStart(2,'0')).join('');
	}

	// ── WCAG ─────────────────────────────────────────────────────────────────

	function luminance(hex) {
		let r=parseInt(hex.slice(1,3),16)/255, g=parseInt(hex.slice(3,5),16)/255, b=parseInt(hex.slice(5,7),16)/255;
		r=sRGBToLinear(r); g=sRGBToLinear(g); b=sRGBToLinear(b);
		return 0.2126*r + 0.7152*g + 0.0722*b;
	}

	function contrastRatio(hexA, hexB) {
		const la=luminance(hexA), lb=luminance(hexB);
		return (Math.max(la,lb)+0.05) / (Math.min(la,lb)+0.05);
	}

	// For a given background and target fg hue+chroma, binary search for the L
	// that meets targetRatio. Searches dark and light halves separately.
	function findContrast(bgHex, H, C, targetRatio) {
		const baseLum = luminance(bgHex);
		function ratio(L) {
			const lum = luminance(oklchToHex(L, C, H));
			return (Math.max(baseLum, lum) + 0.05) / (Math.min(baseLum, lum) + 0.05);
		}
		let lo = 0.02, hi = 0.50;
		for (let i = 0; i < 24; i++) { const mid=(lo+hi)/2; if (ratio(mid)>=targetRatio) lo=mid; else hi=mid; }
		const darkL = lo, darkOk = ratio(darkL) >= targetRatio;

		lo = 0.50; hi = 0.98;
		for (let i = 0; i < 24; i++) { const mid=(lo+hi)/2; if (ratio(mid)>=targetRatio) hi=mid; else lo=mid; }
		const lightL = hi, lightOk = ratio(lightL) >= targetRatio;

		if (!darkOk && !lightOk) return null;
		if (darkOk && lightOk) {
			return {
				dark:  { hex: oklchToHex(darkL,  C, H), ratio: ratio(darkL)  },
				light: { hex: oklchToHex(lightL, C, H), ratio: ratio(lightL) },
			};
		}
		if (darkOk)  return { dark:  { hex: oklchToHex(darkL,  C, H), ratio: ratio(darkL)  } };
		if (lightOk) return { light: { hex: oklchToHex(lightL, C, H), ratio: ratio(lightL) } };
	}

	// ── Parsing ───────────────────────────────────────────────────────────────

	function parseHex(str) {
		str = str.trim().replace(/^#/, '');
		if (str.length === 3) str = str.split('').map(c => c + c).join('');
		return /^[0-9a-fA-F]{6}$/.test(str) ? '#' + str.toLowerCase() : null;
	}

	const bgHex = $derived(parseHex(bgInput));
	const fgHex = $derived(parseHex(fgInput));
	const fgOklch = $derived(fgHex ? hexToOklch(fgHex) : null);
	const bgOklch = $derived(bgHex ? hexToOklch(bgHex) : null);
	const bgLum = $derived(bgHex ? luminance(bgHex) : null);
	let chromaMax = $state(null); // null = auto

	const targetRatio = $derived(level === 'aaa' ? 7 : 4.5);
	const maxChroma = $derived(chromaMax ?? (
		mode === 'bg-edge'
			? (bgOklch ? Math.min(Math.max(bgOklch.C, 0.10), 0.35) : 0.25)
			: (fgOklch ? Math.min(Math.max(fgOklch.C, 0.20), 0.35) : 0.25)
	));

	// Sample 10 chroma steps from near-grey up to maxChroma; show all valid results
	const results = $derived.by(() => {
		if (!bgHex || !fgOklch) return [];
		const out = [];
		const seen = new Set();
		const steps = 10;
		for (let i = 0; i < steps; i++) {
			const C = 0.03 + (i / (steps - 1)) * (maxChroma - 0.03);
			const found = findContrast(bgHex, fgOklch.H, C, targetRatio);
			if (!found) continue;
			for (const candidate of [found.dark, found.light].filter(Boolean)) {
				if (seen.has(candidate.hex)) continue;
				seen.add(candidate.hex);
				out.push({ fg: candidate.hex, ratio: candidate.ratio });
			}
		}
		out.sort((a, b) => hexToOklch(a.fg).C - hexToOklch(b.fg).C);
		return out;
	});

	// For a given background hue, find the lightest background where fgHex text achieves targetRatio.
	// This is the "edge" — anything lighter than this bg and the light text fails.
	const bgEdges = $derived.by(() => {
		if (!bgOklch || !fgHex) return [];
		const out = [];
		const steps = 10;
		const textLum = luminance(fgHex);

		for (let i = 0; i < steps; i++) {
			const C = 0.03 + (i / (steps - 1)) * (maxChroma - 0.03);

			const getRatio = (L) => {
				const lum = luminance(oklchToHex(L, C, bgOklch.H));
				return (Math.max(textLum, lum) + 0.05) / (Math.min(textLum, lum) + 0.05);
			};

			// Binary search: max L where ratio >= targetRatio (higher L = lighter bg = less contrast)
			let lo = 0.02, hi = 0.98;
			for (let j = 0; j < 24; j++) {
				const mid = (lo + hi) / 2;
				if (getRatio(mid) >= targetRatio) lo = mid; else hi = mid;
			}

			const edgeL = lo;
			if (getRatio(edgeL) < targetRatio) continue;
			out.push({ bg: oklchToHex(edgeL, C, bgOklch.H), ratio: getRatio(edgeL), C });
		}

		return out;
	});

	function copy(hex) { navigator.clipboard.writeText(hex); }
	function copyPair(fg) { navigator.clipboard.writeText(JSON.stringify({ bg: bgHex, fg })); }
</script>

<div class="flex flex-col gap-3">
	<!-- Inputs -->
	<div class="flex gap-4 flex-wrap">
		<!-- Background -->
		<div class="flex flex-col gap-1">
			<span class="text-xs text-gray-400 font-medium">Background</span>
			<div class="flex items-center gap-1.5">
				<input type="color"
					value={bgHex ?? '#cccccc'}
					oninput={(e) => bgManual = e.target.value}
					class="w-7 h-7 cursor-pointer border-0 p-0 bg-transparent flex-shrink-0"
				/>
				<input
					type="text"
					value={bgInput}
					oninput={(e) => bgManual = e.target.value}
					placeholder="#ffffff"
					class="font-mono text-sm px-2 py-1 outline-none w-32"
					class:bg-gray-100={!!bgHex}
					class:bg-red-100={!bgHex}
				/>
			</div>
		</div>
		<!-- Foreground reference -->
		<div class="flex flex-col gap-1">
			<span class="text-xs text-gray-400 font-medium">{mode === 'bg-edge' ? 'Foreground (light text)' : 'Foreground (target hue)'}</span>
			<div class="flex items-center gap-1.5">
				<input type="color"
					value={fgHex ?? '#cccccc'}
					oninput={(e) => fgInput = e.target.value}
					class="w-7 h-7 cursor-pointer border-0 p-0 bg-transparent flex-shrink-0"
				/>
				<input
					type="text"
					bind:value={fgInput}
					placeholder="#ff6600"
					class="font-mono text-sm px-2 py-1 outline-none w-32"
					class:bg-gray-100={!!fgHex}
					class:bg-red-100={!fgHex}
				/>
			</div>
		</div>
		<!-- Level -->
		<div class="flex flex-col gap-1">
			<span class="text-xs text-gray-400 font-medium">Level</span>
			<select bind:value={level} class="bg-gray-100 px-2 py-1 text-sm outline-none focus:bg-gray-200 cursor-pointer h-[30px]">
				<option value="aa">AA  4.5:1</option>
				<option value="aaa">AAA  7:1</option>
			</select>
		</div>
		<!-- Mode -->
		<div class="flex flex-col gap-1">
			<span class="text-xs text-gray-400 font-medium">Mode</span>
			<div class="flex h-[30px]">
				<button
					onclick={() => mode = 'fg'}
					class="px-2 py-1 text-xs font-mono cursor-pointer border border-gray-200"
					class:bg-gray-700={mode === 'fg'}
					class:text-white={mode === 'fg'}
					class:bg-gray-100={mode !== 'fg'}
					class:text-gray-600={mode !== 'fg'}
				>text pairs</button>
				<button
					onclick={() => mode = 'bg-edge'}
					class="px-2 py-1 text-xs font-mono cursor-pointer border border-gray-200 border-l-0"
					class:bg-gray-700={mode === 'bg-edge'}
					class:text-white={mode === 'bg-edge'}
					class:bg-gray-100={mode !== 'bg-edge'}
					class:text-gray-600={mode !== 'bg-edge'}
				>bg edge</button>
			</div>
		</div>
		<!-- Chroma -->
		<div class="flex flex-col gap-1">
			<span class="text-xs text-gray-400 font-medium">Max chroma</span>
			<div class="flex items-center gap-1.5 h-[30px]">
				<input type="range" min="0.04" max="0.4" step="0.01"
					value={maxChroma}
					oninput={(e) => chromaMax = +e.target.value}
					class="w-24 cursor-pointer accent-gray-600" />
				<span class="text-xs font-mono text-gray-400 w-8">{maxChroma.toFixed(2)}</span>
				{#if chromaMax !== null}
					<button onclick={() => chromaMax = null}
						class="text-xs text-gray-400 hover:text-gray-700 px-1.5 py-1 bg-gray-100 hover:bg-gray-200 cursor-pointer font-mono">auto</button>
				{/if}
			</div>
		</div>
	</div>

	<!-- Results -->
	{#if mode === 'fg'}
		{#if bgHex && fgOklch}
			{#if results.length === 0}
				<p class="text-xs text-gray-400 font-mono">No valid foreground colours found at this hue and level.</p>
			{:else}
				<div class="flex flex-col gap-0.5">
					{#each results as r}
						<div class="flex items-stretch gap-0.5">
							<button
								onclick={() => copyPair(r.fg)}
								class="flex-1 flex items-center justify-between px-3 cursor-pointer min-w-0"
								style="background:{bgHex}; height:36px;"
								title="Click to copy pair as JSON"
							>
								<span class="font-mono text-xs" style="color:{r.fg};">{r.fg}</span>
								<span class="font-mono text-xs" style="color:{r.fg};">Aa</span>
							</button>
							<div class="flex-shrink-0 flex items-center justify-end w-14">
								<span class="text-xs font-mono text-gray-400">{r.ratio.toFixed(1)}</span>
							</div>
							<button
								onclick={() => copy(r.fg)}
								title={r.fg}
								class="flex-shrink-0 cursor-pointer"
								style="background:{r.fg}; width:36px; height:36px;"
							></button>
						</div>
					{/each}
				</div>
			{/if}
		{/if}
	{:else if mode === 'bg-edge'}
		{#if fgOklch}
			{#if bgEdges.length === 0}
				<p class="text-xs text-gray-400 font-mono">No valid background edges found at this hue and level.</p>
			{:else}
				<p class="text-xs text-gray-400 font-mono mb-1">Lightest background at each chroma where <span class="font-bold" style="color:{fgHex}">{fgHex}</span> text still passes.</p>
				<div class="flex flex-col gap-0.5">
					{#each bgEdges as e}
						<div class="flex items-stretch gap-0.5">
							<button
								onclick={() => copy(e.bg)}
								class="flex-1 flex items-center justify-between px-3 cursor-pointer min-w-0"
								style="background:{e.bg}; height:36px;"
								title="Click to copy background hex"
							>
								<span class="font-mono text-xs" style="color:{fgHex}">{e.bg}</span>
								<span class="font-mono text-xs" style="color:{fgHex}">Aa</span>
							</button>
							<div class="flex-shrink-0 flex items-center justify-end w-14">
								<span class="text-xs font-mono text-gray-400">{e.ratio.toFixed(1)}</span>
							</div>
							<div class="flex-shrink-0 flex items-center justify-end w-10">
								<span class="text-xs font-mono text-gray-300">C{e.C.toFixed(2)}</span>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		{/if}
	{/if}
</div>
