<script>
	let { colour } = $props();

	let count = $state(5);
	let mode = $state('oklch');

	// ── OKLCH ────────────────────────────────────────────────────────────────

	function sRGBToLinear(c) { return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; }
	function linearToSRGB(c) { return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; }

	function hexToOklch(hex) {
		let r = parseInt(hex.slice(1,3),16)/255, g = parseInt(hex.slice(3,5),16)/255, b = parseInt(hex.slice(5,7),16)/255;
		r = sRGBToLinear(r); g = sRGBToLinear(g); b = sRGBToLinear(b);
		const l = Math.cbrt(0.4122214708*r+0.5363325363*g+0.0514459929*b);
		const m = Math.cbrt(0.2119034982*r+0.6806995451*g+0.1073969566*b);
		const s = Math.cbrt(0.0883024619*r+0.2817188376*g+0.6299787005*b);
		const L=0.2104542553*l+0.7936177850*m-0.0040720468*s;
		const a=1.9779984951*l-2.4285922050*m+0.4505937099*s;
		const bv=0.0259040371*l+0.7827717662*m-0.8086757660*s;
		return { L, C: Math.sqrt(a*a+bv*bv), H: (Math.atan2(bv,a)*180/Math.PI+360)%360 };
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
		const clamp = v => Math.round(Math.min(1,Math.max(0,v))*255);
		return '#'+[clamp(r),clamp(g),clamp(b)].map(v=>v.toString(16).padStart(2,'0')).join('');
	}

	// ── HSL ──────────────────────────────────────────────────────────────────

	function hexToHsl(hex) {
		let r=parseInt(hex.slice(1,3),16)/255, g=parseInt(hex.slice(3,5),16)/255, b=parseInt(hex.slice(5,7),16)/255;
		const max=Math.max(r,g,b), min=Math.min(r,g,b);
		let h, s, l=(max+min)/2;
		if (max===min) { h=s=0; } else {
			const d=max-min; s=l>0.5?d/(2-max-min):d/(max+min);
			switch(max) {
				case r: h=((g-b)/d+(g<b?6:0))/6; break;
				case g: h=((b-r)/d+2)/6; break;
				case b: h=((r-g)/d+4)/6; break;
			}
		}
		return { h:h*360, s:s*100, l:l*100 };
	}

	function hslToHex(h, s, l) {
		s/=100; l/=100;
		const a=s*Math.min(l,1-l);
		const f=n=>{ const k=(n+h/30)%12; return l-a*Math.max(Math.min(k-3,9-k,1),-1); };
		const clamp=v=>Math.round(Math.min(1,Math.max(0,v))*255);
		return '#'+[f(0),f(8),f(4)].map(v=>clamp(v).toString(16).padStart(2,'0')).join('');
	}

	// ── HSV ──────────────────────────────────────────────────────────────────

	function hexToHsv(hex) {
		let r=parseInt(hex.slice(1,3),16)/255, g=parseInt(hex.slice(3,5),16)/255, b=parseInt(hex.slice(5,7),16)/255;
		const max=Math.max(r,g,b), min=Math.min(r,g,b), d=max-min;
		let h=0;
		if (d) switch(max) {
			case r: h=((g-b)/d+(g<b?6:0))/6; break;
			case g: h=((b-r)/d+2)/6; break;
			case b: h=((r-g)/d+4)/6; break;
		}
		return { h:h*360, s:max?d/max*100:0, v:max*100 };
	}

	function hsvToHex(h, s, v) {
		s/=100; v/=100;
		const i=Math.floor(h/60)%6, f=h/60-Math.floor(h/60);
		const p=v*(1-s), q=v*(1-f*s), t=v*(1-(1-f)*s);
		const [r,g,b]=[[v,t,p],[q,v,p],[p,v,t],[p,q,v],[t,p,v],[v,p,q]][i];
		const clamp=v=>Math.round(Math.min(1,Math.max(0,v))*255);
		return '#'+[r,g,b].map(v=>clamp(v).toString(16).padStart(2,'0')).join('');
	}

	// ── HWB ──────────────────────────────────────────────────────────────────

	function hexToHwb(hex) {
		let r=parseInt(hex.slice(1,3),16)/255, g=parseInt(hex.slice(3,5),16)/255, b=parseInt(hex.slice(5,7),16)/255;
		const max=Math.max(r,g,b), min=Math.min(r,g,b);
		let h=0;
		if (max!==min) { const d=max-min; switch(max) {
			case r: h=((g-b)/d+(g<b?6:0))/6; break;
			case g: h=((b-r)/d+2)/6; break;
			case b: h=((r-g)/d+4)/6; break;
		}}
		return { h:h*360, w:min*100, bk:(1-max)*100 };
	}

	function hwbToHex(h, w, bk) {
		w/=100; bk/=100;
		if (w+bk>=1) { const g=Math.round(w/(w+bk)*255); return '#'+[g,g,g].map(x=>x.toString(16).padStart(2,'0')).join(''); }
		const f=n=>{ const k=(n+h/30)%12; return 0.5-0.5*Math.max(Math.min(k-3,9-k,1),-1); };
		const sc=1-w-bk;
		const clamp=v=>Math.round(Math.min(1,Math.max(0,v))*255);
		return '#'+[f(0),f(8),f(4)].map(ch=>clamp(ch*sc+w).toString(16).padStart(2,'0')).join('');
	}

	// ── Mode-aware ops ────────────────────────────────────────────────────────

	const pos = (i, n) => n <= 1 ? 0.5 : i / (n - 1);

	function baseHue(hex) {
		if (mode==='oklch') return hexToOklch(hex).H;
		if (mode==='hsv')   return hexToHsv(hex).h;
		if (mode==='hwb')   return hexToHwb(hex).h;
		return hexToHsl(hex).h;
	}

	function withHue(hex, newH) {
		const h = (newH + 360) % 360;
		if (mode==='oklch') { const {L,C}=hexToOklch(hex); return oklchToHex(L,C,h); }
		if (mode==='hsv')   { const {s,v}=hexToHsv(hex);   return hsvToHex(h,s,v); }
		if (mode==='hwb')   { const {w,bk}=hexToHwb(hex);  return hwbToHex(h,w,bk); }
		const {s,l}=hexToHsl(hex); return hslToHex(h,s,l);
	}

	// ── Palette generators ────────────────────────────────────────────────────

	function interpolateHue(hex, fromOff, toOff, n) {
		const H = baseHue(hex);
		return Array.from({length:n}, (_,i) => withHue(hex, H+fromOff+pos(i,n)*(toOff-fromOff)));
	}

	function cycleHues(hex, offsets, n) {
		// Cap at number of unique offsets so colours don't repeat
		const count = Math.min(n, offsets.length);
		const H = baseHue(hex);
		return Array.from({length:count}, (_,i) => withHue(hex, H+offsets[i]));
	}

	function tintsShades(hex, n) {
		if (mode==='oklch') {
			const {C,H}=hexToOklch(hex);
			return Array.from({length:n}, (_,i) => oklchToHex(0.1+pos(i,n)*0.8, C, H));
		}
		if (mode==='hsv') {
			const {h,s}=hexToHsv(hex);
			return Array.from({length:n}, (_,i) => hsvToHex(h, s, 5+pos(i,n)*90));
		}
		if (mode==='hwb') {
			const {h}=hexToHwb(hex);
			return Array.from({length:n}, (_,i) => hwbToHex(h, pos(i,n)*85, (1-pos(i,n))*85));
		}
		const {h,s}=hexToHsl(hex);
		return Array.from({length:n}, (_,i) => hslToHex(h, s, 5+pos(i,n)*90));
	}

	function temperature(hex, n) {
		if (mode==='oklch') {
			const {L,C}=hexToOklch(hex);
			return Array.from({length:n}, (_,i) => oklchToHex(L, C, 30+pos(i,n)*180));
		}
		if (mode==='hsv') {
			const {s,v}=hexToHsv(hex);
			return Array.from({length:n}, (_,i) => hsvToHex(30+pos(i,n)*180, s, v));
		}
		if (mode==='hwb') {
			const {w,bk}=hexToHwb(hex);
			return Array.from({length:n}, (_,i) => hwbToHex(30+pos(i,n)*180, w, bk));
		}
		const {s,l}=hexToHsl(hex);
		return Array.from({length:n}, (_,i) => hslToHex(30+pos(i,n)*180, s, l));
	}

	function sequential(hex, n, role) {
		if (mode==='oklch') {
			const {L,C,H}=hexToOklch(hex);
			let Ls, Le;
			if      (role==='dark')  { Ls=L;    Le=0.95; }
			else if (role==='light') { Ls=0.05; Le=L; }
			else { const r=Math.min(L-0.05,0.95-L); Ls=L-r; Le=L+r; }
			return Array.from({length:n}, (_,i) => oklchToHex(Math.max(0.05,Math.min(0.95,Ls+pos(i,n)*(Le-Ls))), C, H));
		}
		if (mode==='hsv') {
			const {h,s,v}=hexToHsv(hex);
			let vs, ve;
			if      (role==='dark')  { vs=v;  ve=95; }
			else if (role==='light') { vs=5;  ve=v; }
			else { const r=Math.min(v-5,95-v); vs=v-r; ve=v+r; }
			return Array.from({length:n}, (_,i) => hsvToHex(h, s, Math.max(5,Math.min(95,vs+pos(i,n)*(ve-vs)))));
		}
		if (mode==='hwb') {
			const {h,w,bk}=hexToHwb(hex);
			let ws, we, bks, bke;
			if      (role==='dark')  { ws=w;  we=85; bks=bk; bke=0; }
			else if (role==='light') { ws=0;  we=w;  bks=85; bke=bk; }
			else { const r=Math.min(w,bk,40); ws=w-r; we=w+r; bks=bk+r; bke=bk-r; }
			return Array.from({length:n}, (_,i) => hwbToHex(h, Math.max(0,ws+pos(i,n)*(we-ws)), Math.max(0,bks+pos(i,n)*(bke-bks))));
		}
		const {h,s,l}=hexToHsl(hex);
		let ls, le;
		if      (role==='dark')  { ls=l;  le=95; }
		else if (role==='light') { ls=5;  le=l; }
		else { const r=Math.min(l-5,95-l); ls=l-r; le=l+r; }
		return Array.from({length:n}, (_,i) => hslToHex(h, s, Math.max(5,Math.min(95,ls+pos(i,n)*(le-ls)))));
	}

	// ── Rows ─────────────────────────────────────────────────────────────────

	const rows = $derived([
		{ label: 'Complementary',  colours: interpolateHue(colour, 0, 180, count) },
		{ label: 'Triadic',        colours: cycleHues(colour, [0, 120, 240], count) },
		{ label: 'Analogous',      colours: interpolateHue(colour, -30, 30, count) },
		{ label: 'Split-comp',     colours: cycleHues(colour, [0, 150, 210], count) },
		{ label: 'Tetradic',       colours: cycleHues(colour, [0, 90, 180, 270], count) },
		{ label: 'Tints & shades', colours: tintsShades(colour, count) },
		{ label: 'Temperature',    colours: temperature(colour, count) },
		{ label: 'Seq dark',       colours: sequential(colour, count, 'dark') },
		{ label: 'Seq light',      colours: sequential(colour, count, 'light') },
		{ label: 'Seq mid',        colours: sequential(colour, count, 'mid') },
	]);

	function copy(hex) { navigator.clipboard.writeText(hex); }
	function copyRow(colours) { navigator.clipboard.writeText(JSON.stringify(colours)); }
</script>

<div class="flex flex-col gap-3">
	<div class="flex items-center gap-6">
		<div class="flex items-center gap-2">
			<span class="text-xs text-gray-400 font-medium">Count</span>
			<input type="number" min="1" max="10" bind:value={count}
				class="w-12 bg-gray-100 px-2 py-1 text-sm font-mono outline-none focus:bg-gray-200 text-center" />
		</div>
		<div class="flex items-center gap-2">
			<span class="text-xs text-gray-400 font-medium">Mode</span>
			<select bind:value={mode} class="bg-gray-100 px-2 py-1 text-sm outline-none focus:bg-gray-200 cursor-pointer">
				<option value="oklch">OKLCH</option>
				<option value="hsl">HSL</option>
				<option value="hsv">HSV</option>
				<option value="hwb">HWB</option>
			</select>
		</div>
	</div>

	<div class="flex flex-col gap-0.5">
		{#each rows as row}
			<div class="flex items-stretch">
				<div class="w-24 flex-shrink-0 flex items-center">
					<button onclick={() => copyRow(row.colours)}
						class="text-xs text-gray-400 leading-tight cursor-pointer hover:text-gray-700 text-left"
					>{row.label}</button>
				</div>
				<div class="flex flex-1 min-w-0">
					{#each row.colours as hex}
						<button onclick={() => copy(hex)} title={hex}
							class="flex-1 cursor-pointer"
							style="background:{hex}; height:28px;"
						></button>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>
