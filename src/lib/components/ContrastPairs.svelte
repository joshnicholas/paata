<script>
	let { colour } = $props();

	let count = $state(6);
	let level = $state('aa'); // 'aa' = 4.5:1, 'aaa' = 7:1
	let baseRole = $state('bg'); // 'bg' = colour is background, 'fg' = colour is foreground

	// ── OKLCH (used for generation) ───────────────────────────────────────────

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

	// ── WCAG luminance & contrast ─────────────────────────────────────────────

	function luminance(hex) {
		let r=parseInt(hex.slice(1,3),16)/255, g=parseInt(hex.slice(3,5),16)/255, b=parseInt(hex.slice(5,7),16)/255;
		r=sRGBToLinear(r); g=sRGBToLinear(g); b=sRGBToLinear(b);
		return 0.2126*r + 0.7152*g + 0.0722*b;
	}

	function contrastRatio(hexA, hexB) {
		const la=luminance(hexA), lb=luminance(hexB);
		return (Math.max(la,lb)+0.05) / (Math.min(la,lb)+0.05);
	}

	// Binary search for an OKLCH colour at (targetH, chroma) whose contrast
	// with baseHex meets targetRatio. Searches both dark and light directions.
	function findContrast(baseHex, targetH, chroma, targetRatio) {
		const baseLum = luminance(baseHex);

		function ratio(L) {
			const lum = luminance(oklchToHex(L, chroma, targetH));
			return (Math.max(baseLum, lum)+0.05) / (Math.min(baseLum, lum)+0.05);
		}

		// Find darkest acceptable light colour (min L in light range)
		let lo=0.50, hi=0.98;
		for (let i=0; i<24; i++) {
			const mid=(lo+hi)/2;
			if (ratio(mid)>=targetRatio) hi=mid; else lo=mid;
		}
		const lightL=hi, lightRatio=ratio(lightL);

		// Find lightest acceptable dark colour (max L in dark range)
		lo=0.02; hi=0.50;
		for (let i=0; i<24; i++) {
			const mid=(lo+hi)/2;
			if (ratio(mid)>=targetRatio) lo=mid; else hi=mid;
		}
		const darkL=lo, darkRatio=ratio(darkL);

		const lightOk = lightRatio >= targetRatio;
		const darkOk  = darkRatio  >= targetRatio;

		if (lightOk && darkOk) {
			// Return both — let caller decide
			return {
				dark:  { hex: oklchToHex(darkL,  chroma, targetH), ratio: darkRatio },
				light: { hex: oklchToHex(lightL, chroma, targetH), ratio: lightRatio },
			};
		}
		if (lightOk) return { light: { hex: oklchToHex(lightL, chroma, targetH), ratio: lightRatio } };
		if (darkOk)  return { dark:  { hex: oklchToHex(darkL,  chroma, targetH), ratio: darkRatio } };
		return null;
	}

	// ── Derived pairs ─────────────────────────────────────────────────────────

	const targetRatio = $derived(level === 'aaa' ? 7 : 4.5);

	// Use the base colour's chroma, floored to a minimum so greys still produce vivid pairs
	const chroma = $derived(Math.max(hexToOklch(colour).C, 0.08));

	const pairs = $derived.by(() => {
		const results = [];
		for (let i = 0; i < count; i++) {
			const hue = (i / count) * 360;
			const found = findContrast(colour, hue, chroma, targetRatio);
			if (!found) continue;

			const candidate = (found.dark && found.light)
				? (found.dark.ratio > found.light.ratio ? found.dark : found.light)
				: (found.dark ?? found.light);

			const bg = baseRole === 'bg' ? colour : candidate.hex;
			const fg = baseRole === 'bg' ? candidate.hex : colour;
			results.push({ bg, fg, ratio: contrastRatio(bg, fg), hue });
		}
		return results;
	});

	function copy(hex) { navigator.clipboard.writeText(hex); }
	function copyPair(bg, fg) { navigator.clipboard.writeText(JSON.stringify({ bg, fg })); }
</script>

<div class="flex flex-col gap-3">
	<!-- Controls -->
	<div class="flex items-center gap-6 flex-wrap">
		<div class="flex items-center gap-2">
			<span class="text-xs text-gray-400 font-medium">Count</span>
			<input type="number" min="1" max="12" bind:value={count}
				class="w-12 bg-gray-100 px-2 py-1 text-sm font-mono outline-none focus:bg-gray-200 text-center" />
		</div>
		<div class="flex items-center gap-2">
			<span class="text-xs text-gray-400 font-medium">Level</span>
			<select bind:value={level} class="bg-gray-100 px-2 py-1 text-sm outline-none focus:bg-gray-200 cursor-pointer">
				<option value="aa">AA  4.5:1</option>
				<option value="aaa">AAA  7:1</option>
			</select>
		</div>
		<div class="flex items-center gap-2">
			<span class="text-xs text-gray-400 font-medium">Base is</span>
			<select bind:value={baseRole} class="bg-gray-100 px-2 py-1 text-sm outline-none focus:bg-gray-200 cursor-pointer">
				<option value="bg">background</option>
				<option value="fg">foreground</option>
			</select>
		</div>
	</div>

	<!-- Pairs -->
	<div class="flex flex-col gap-0.5">
		{#each pairs as pair}
			<div class="flex items-stretch gap-0.5">
				<!-- Full-width preview: bg with fg text -->
				<button
					onclick={() => copyPair(pair.bg, pair.fg)}
					class="flex-1 flex items-center justify-between px-3 cursor-pointer min-w-0"
					style="background:{pair.bg}; height:36px;"
					title="Click to copy pair as JSON"
				>
					<span class="font-mono text-xs" style="color:{pair.fg};">{pair.fg}</span>
					<span class="font-mono text-xs" style="color:{pair.fg};">Aa</span>
				</button>
				<!-- Ratio badge -->
				<div class="flex-shrink-0 flex items-center justify-end w-14">
					<span class="text-xs font-mono text-gray-400">{pair.ratio.toFixed(1)}</span>
				</div>
				<!-- FG swatch -->
				<button
					onclick={() => copy(pair.fg)}
					title={pair.fg}
					class="flex-shrink-0 cursor-pointer"
					style="background:{pair.fg}; width:36px; height:36px;"
				></button>
			</div>
		{/each}
	</div>
</div>
