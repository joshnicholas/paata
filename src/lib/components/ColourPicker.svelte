<script>
	import { onMount } from 'svelte';

	let { oncolour } = $props();

	const HEIGHT = 300;
	const HUE_HEIGHT = 24;

	let pickerWrapper;
	let canvas;
	let hueCanvas;

	let cursorX = $state(0);
	let cursorY = $state(0);
	let hue = $state(0);
	let isDragging = false;
	let hueDragging = false;

	let hexInput = $state('#ff0000');
	let rgbInput = $state('255, 0, 0');
	let hslInput = $state('0°, 100%, 50%');

	$effect(() => { oncolour?.(hexInput); });

	function drawPicker() {
		if (!canvas) return;
		const ctx = canvas.getContext('2d');
		const w = canvas.width, h = canvas.height;
		const colourGrad = ctx.createLinearGradient(0, 0, w, 0);
		colourGrad.addColorStop(0, 'white');
		colourGrad.addColorStop(1, `hsl(${hue}, 100%, 50%)`);
		ctx.fillStyle = colourGrad;
		ctx.fillRect(0, 0, w, h);
		const darkGrad = ctx.createLinearGradient(0, 0, 0, h);
		darkGrad.addColorStop(0, 'rgba(0,0,0,0)');
		darkGrad.addColorStop(1, 'rgba(0,0,0,1)');
		ctx.fillStyle = darkGrad;
		ctx.fillRect(0, 0, w, h);
	}

	function drawHueBar() {
		if (!hueCanvas) return;
		const ctx = hueCanvas.getContext('2d');
		const grad = ctx.createLinearGradient(0, 0, hueCanvas.width, 0);
		for (let i = 0; i <= 360; i += 10) {
			grad.addColorStop(i / 360, `hsl(${i}, 100%, 50%)`);
		}
		ctx.fillStyle = grad;
		ctx.fillRect(0, 0, hueCanvas.width, hueCanvas.height);
	}

	function sampleColour(x, y) {
		if (!canvas) return;
		const ctx = canvas.getContext('2d');
		const px = Math.round(Math.max(0, Math.min(canvas.width - 1, x)));
		const py = Math.round(Math.max(0, Math.min(canvas.height - 1, y)));
		const [r, g, b] = ctx.getImageData(px, py, 1, 1).data;
		hexInput = rgbToHex(r, g, b);
		rgbInput = `${r}, ${g}, ${b}`;
		const hsl = rgbToHsl(r, g, b);
		hslInput = `${hsl.h}°, ${hsl.s}%, ${hsl.l}%`;
	}

	function rgbToHex(r, g, b) {
		return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
	}

	function rgbToHsl(r, g, b) {
		r /= 255; g /= 255; b /= 255;
		const max = Math.max(r, g, b), min = Math.min(r, g, b);
		let h, s, l = (max + min) / 2;
		if (max === min) {
			h = s = 0;
		} else {
			const d = max - min;
			s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
			switch (max) {
				case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
				case g: h = ((b - r) / d + 2) / 6; break;
				case b: h = ((r - g) / d + 4) / 6; break;
			}
		}
		return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
	}

	function rgbToHsv(r, g, b) {
		r /= 255; g /= 255; b /= 255;
		const max = Math.max(r, g, b), min = Math.min(r, g, b);
		const v = max;
		const s = max === 0 ? 0 : (max - min) / max;
		let h = 0;
		if (max !== min) {
			const d = max - min;
			switch (max) {
				case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
				case g: h = ((b - r) / d + 2) / 6; break;
				case b: h = ((r - g) / d + 4) / 6; break;
			}
		}
		return { h: Math.round(h * 360), s, v };
	}

	function hslToRgb(h, s, l) {
		s /= 100; l /= 100;
		const c = (1 - Math.abs(2 * l - 1)) * s;
		const x = c * (1 - Math.abs((h / 60) % 2 - 1));
		const m = l - c / 2;
		let r, g, b;
		if (h < 60)       [r, g, b] = [c, x, 0];
		else if (h < 120) [r, g, b] = [x, c, 0];
		else if (h < 180) [r, g, b] = [0, c, x];
		else if (h < 240) [r, g, b] = [0, x, c];
		else if (h < 300) [r, g, b] = [x, 0, c];
		else              [r, g, b] = [c, 0, x];
		return { r: Math.round((r + m) * 255), g: Math.round((g + m) * 255), b: Math.round((b + m) * 255) };
	}

	function applyRgb(r, g, b) {
		const hsv = rgbToHsv(r, g, b);
		hue = hsv.h;
		cursorX = hsv.s * canvas.width;
		cursorY = (1 - hsv.v) * HEIGHT;
		drawPicker();
		sampleColour(cursorX, cursorY);
	}

	function parseAndApplyHex(str) {
		str = str.trim().replace(/^#/, '');
		if (str.length === 3) str = str.split('').map(c => c + c).join('');
		if (!/^[0-9a-fA-F]{6}$/.test(str)) return;
		applyRgb(parseInt(str.slice(0, 2), 16), parseInt(str.slice(2, 4), 16), parseInt(str.slice(4, 6), 16));
	}

	function parseAndApplyRgb(str) {
		const m = str.match(/(\d+)\D+(\d+)\D+(\d+)/);
		if (!m) return;
		applyRgb(+m[1], +m[2], +m[3]);
	}

	function parseAndApplyHsl(str) {
		const m = str.match(/([\d.]+)[^\d.]+([\d.]+)[^\d.]+([\d.]+)/);
		if (!m) return;
		const { r, g, b } = hslToRgb(+m[1], +m[2], +m[3]);
		applyRgb(r, g, b);
	}

	// Scale mouse/touch CSS coords to canvas pixel coords
	function getPos(e, el) {
		const rect = el.getBoundingClientRect();
		const scaleX = el.width / rect.width;
		const scaleY = el.height / rect.height;
		const clientX = e.touches ? e.touches[0].clientX : e.clientX;
		const clientY = e.touches ? e.touches[0].clientY : e.clientY;
		return {
			x: Math.max(0, Math.min(el.width - 1, (clientX - rect.left) * scaleX)),
			y: Math.max(0, Math.min(el.height - 1, (clientY - rect.top) * scaleY))
		};
	}

	function onPickerDown(e) {
		isDragging = true;
		const { x, y } = getPos(e, canvas);
		cursorX = x; cursorY = y;
		sampleColour(x, y);
	}

	function onPickerMove(e) {
		if (!isDragging) return;
		const { x, y } = getPos(e, canvas);
		cursorX = x; cursorY = y;
		sampleColour(x, y);
	}

	function onPickerUp() { isDragging = false; }

	function onHueDown(e) {
		hueDragging = true;
		updateHue(e);
	}

	function onHueMove(e) {
		if (!hueDragging) return;
		updateHue(e);
	}

	function onHueUp() { hueDragging = false; }

	function updateHue(e) {
		const rect = hueCanvas.getBoundingClientRect();
		const clientX = e.touches ? e.touches[0].clientX : e.clientX;
		const x = Math.max(0, Math.min(hueCanvas.width - 1, (clientX - rect.left) * (hueCanvas.width / rect.width)));
		hue = Math.round((x / hueCanvas.width) * 360);
		drawPicker();
		sampleColour(cursorX, cursorY);
	}

	function copy(text) {
		navigator.clipboard.writeText(text);
	}

	onMount(() => {
		const w = pickerWrapper.clientWidth;
		// Set dimensions imperatively — do NOT bind width as reactive state or
		// Svelte will re-render the canvas element (clearing it) after onMount draws.
		canvas.width = w;
		canvas.height = HEIGHT;
		hueCanvas.width = w;
		hueCanvas.height = HUE_HEIGHT;
		drawPicker();
		drawHueBar();
		sampleColour(0, 0);
	});
</script>

<svelte:window
	onmousemove={(e) => { onPickerMove(e); onHueMove(e); }}
	onmouseup={() => { onPickerUp(); onHueUp(); }}
	ontouchmove={(e) => { onPickerMove(e); onHueMove(e); }}
	ontouchend={() => { onPickerUp(); onHueUp(); }}
/>

<div bind:this={pickerWrapper} class="flex flex-col w-full overflow-hidden">
	<!-- Picker canvas — width/height set imperatively in onMount, not via reactive bindings -->
	<div class="relative select-none w-full" style="height:{HEIGHT}px;">
		<canvas
			bind:this={canvas}
			class="block w-full h-full cursor-crosshair"
			style="touch-action: none;"
			draggable="false"
			onmousedown={onPickerDown}
			ontouchstart={onPickerDown}
		></canvas>
		<div
			class="absolute w-3 h-3 rounded-full border-2 border-white shadow pointer-events-none -translate-x-1/2 -translate-y-1/2"
			style="left:{cursorX}px; top:{cursorY}px; background:{hexInput};"
		></div>
	</div>

	<!-- Hue bar -->
	<div class="relative select-none w-full" style="height:{HUE_HEIGHT}px;">
		<canvas
			bind:this={hueCanvas}
			class="block w-full h-full cursor-pointer"
			style="touch-action: none;"
			draggable="false"
			onmousedown={onHueDown}
			ontouchstart={onHueDown}
		></canvas>
		<div
			class="absolute top-0 w-0.5 h-full bg-white border-x border-black/20 pointer-events-none -translate-x-1/2 shadow"
			style="left:{(hue / 360) * 100}%;"
		></div>
	</div>

	<!-- Info row: swatch fills space, inputs column is as narrow as content needs -->
	<div class="flex gap-3 mt-4 items-stretch min-w-0">
		<!-- Inputs — shrink-0, width driven by content -->
		<div class="flex flex-col gap-1.5 flex-shrink-0 min-w-0">
			{#each [
				{ label: 'HEX', value: hexInput, apply: parseAndApplyHex, set: (v) => hexInput = v },
				{ label: 'RGB', value: rgbInput, apply: parseAndApplyRgb, set: (v) => rgbInput = v },
				{ label: 'HSL', value: hslInput, apply: parseAndApplyHsl, set: (v) => hslInput = v },
			] as field}
				<div class="flex items-center gap-1.5">
					<span class="text-xs text-gray-400 font-medium w-7 flex-shrink-0">{field.label}</span>
					<input
						type="text"
						class="font-mono text-sm bg-gray-100 px-2 py-1 outline-none focus:bg-gray-200 w-40"
						value={field.value}
						oninput={(e) => field.set(e.target.value)}
						onblur={(e) => field.apply(e.target.value)}
						onkeydown={(e) => e.key === 'Enter' && field.apply(e.target.value)}
					/>
					<button
						onclick={() => copy(field.value)}
						class="text-xs text-gray-400 hover:text-gray-700 px-1.5 py-1 bg-gray-100 hover:bg-gray-200 flex-shrink-0 cursor-pointer font-mono"
					>c</button>
				</div>
			{/each}
		</div>

		<!-- Swatch — fills remaining space -->
		<div class="flex-1 min-w-0" style="background:{hexInput};"></div>
	</div>
</div>
