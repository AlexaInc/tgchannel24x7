const youtubedl = require('youtube-dl-exec');
const fs = require('fs');

const videoId = process.argv[2];
if (!videoId) {
    console.error('No video ID provided');
    process.exit(1);
}

const proxy = process.env.PROXY_URL;
const cookies = fs.existsSync('cookies.txt') ? 'cookies.txt' : null;

const options = {
    dumpSingleJson: true,
    noWarnings: true,
    noCallHome: true,
    noCheckCertificate: true,
    format: 'bestaudio/best',
    youtubeSkipDashManifest: true,
    referer: 'https://www.youtube.com/',
    forceIpv4: true,
};

if (proxy) options.proxy = proxy;
if (cookies) options.cookiefile = cookies;

// Disable oauth2 explicitly in extractor args style
options.extractorArgs = 'youtube:skip=oauth2';

youtubedl(`https://www.youtube.com/watch?v=${videoId}`, options)
    .then(output => {
        console.log(JSON.stringify(output));
    })
    .catch(err => {
        console.error(err);
        process.exit(1);
    });
