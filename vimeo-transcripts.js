
(async function () {
    // 1) Replace this with your actual WebVTT URL:
    const VTT_URL = "https://player.vimeo.com/texttrack/196587865.vtt?token=6770ef93_0x33b40113aee4d7cbb80eac1edc97ab5457002968";

    // 2) Fetch the .vtt file as text
    const response = await fetch(VTT_URL);
    if (!response.ok) {
        console.error("Error fetching VTT file:", response.statusText);
        return;
    }
    const rawVtt = await response.text();

    // 3) Transform the raw VTT into plain text
    //    - Remove the "WEBVTT" header
    //    - Remove lines that are numeric IDs
    //    - Remove lines that have timestamps --> timestamps
    //    - Cleanup extra blank lines
    const textOnly = rawVtt
        .replace(/^WEBVTT[^\n]*\n+/i, "")              // remove "WEBVTT" header line
        .replace(/^\d+\s*$/gm, "")                    // remove lines that are just numbers (cue IDs)
        .replace(/(\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}).*/g, "") // remove timestamp lines
        .replace(/\n{2,}/g, "\n")                     // collapse multiple blank lines
        .trim();

    // 4) Download as a text file
    const blob = new Blob([textOnly], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "transcript.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log("Transcript downloaded as transcript.txt!");
})();