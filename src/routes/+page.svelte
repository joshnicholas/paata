<script>
	import ColourPicker from '$lib/components/ColourPicker.svelte';
	import ColourHarmonies from '$lib/components/ColourHarmonies.svelte';
	import ContrastPairs from '$lib/components/ContrastPairs.svelte';

	let colour = $state('#ff0000');
</script>

<main class="min-h-screen bg-white py-12 px-6">
	<div class="max-w-[800px] mx-auto flex flex-col gap-12">
		<ColourPicker oncolour={(c) => colour = c} />
		<ColourHarmonies {colour} />
		<ContrastPairs {colour} />
	</div>
</main>
