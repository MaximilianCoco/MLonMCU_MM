/**
 * WhatsApp Image Downloader
 * =========================
 * Downloads all images from the last message sent by a contact.
 *
 * Usage:
 *   node wa-download.js "Contact Name"
 *   node wa-download.js "Contact Name" C:\path\to\output\folder
 *
 * Setup (one time):
 *   npm install
 *   npx puppeteer browsers install chrome-headless-shell
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs     = require('fs');
const path   = require('path');

// --------------------------------------------------------------------------
// Find chrome-headless-shell by recursively scanning the puppeteer cache.
// This works regardless of the exact subfolder name puppeteer uses.
// --------------------------------------------------------------------------
function findHeadlessShell() {
    const cacheRoot = path.join(
        process.env['USERPROFILE'] || process.env['HOME'] || 'C:\\Users\\' + process.env['USERNAME'],
        '.cache', 'puppeteer', 'chrome-headless-shell'
    );

    if (!fs.existsSync(cacheRoot)) return null;

    // Recursively walk the cache folder and return the first .exe found
    function walk(dir) {
        let entries;
        try { entries = fs.readdirSync(dir); } catch (_) { return null; }
        for (const entry of entries) {
            const full = path.join(dir, entry);
            let stat;
            try { stat = fs.statSync(full); } catch (_) { continue; }
            if (stat.isDirectory()) {
                const found = walk(full);
                if (found) return found;
            } else if (entry.toLowerCase() === 'chrome-headless-shell.exe') {
                return full;
            }
        }
        return null;
    }

    return walk(cacheRoot);
}

// --------------------------------------------------------------------------
// Arguments
// --------------------------------------------------------------------------
const contactArg = process.argv[2];
const outputArg  = process.argv[3];

if (!contactArg) {
    console.error('\nUsage:  node wa-download.js "Contact Name" [output-folder]');
    console.error('Example: node wa-download.js "Anna Mueller" C:\\Users\\You\\Desktop\\photos\n');
    process.exit(1);
}

const CONTACT_NAME = contactArg.trim();
const OUTPUT_DIR   = outputArg
    ? path.resolve(outputArg)
    : path.join(process.cwd(), 'whatsapp_images');

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const timestamp = () => new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

// --------------------------------------------------------------------------
// Locate browser
// --------------------------------------------------------------------------
const shellPath = findHeadlessShell();

if (!shellPath) {
    console.error('\nchrome-headless-shell not found in Puppeteer cache.');
    console.error('Run this once to install it:\n');
    console.error('  npx puppeteer browsers install chrome-headless-shell\n');
    process.exit(1);
}

console.log('\nBrowser : ' + shellPath);

// --------------------------------------------------------------------------
// WhatsApp client
// --------------------------------------------------------------------------
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        executablePath: shellPath,
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-first-run',
        ],
    },
});

setInterval(async () => {
    try {
        const state = await client.getState();
        console.log('HEARTBEAT STATE:', state);
    } catch (e) {
        console.log('HEARTBEAT ERROR:', e.message);
    }
}, 5000);



// --------------------------------------------------------------------------
// Events
// --------------------------------------------------------------------------
client.on('qr', (qr) => {
    console.log('\n------------------------------------------');
    console.log('Scan this QR code with WhatsApp on your phone:');
    console.log('(WhatsApp > Menu > Linked Devices > Link a Device)');
    console.log('------------------------------------------\n');
    qrcode.generate(qr, { small: true });
    console.log('\nWaiting for scan...\n');
});

client.on('authenticated', () => {
    console.log('Authenticated (session saved -- no QR needed next time)');
});

client.on('loading_screen', (percent, message) => {
    process.stdout.write('\rLoading WhatsApp... ' + percent + '%   ');
});

client.on('auth_failure', (msg) => {
    console.error('\nAuthentication failed:', msg);
    console.error('Delete the .wwebjs_auth folder and try again.');
    process.exit(1);
});

client.on('disconnected', (reason) => {
    console.error('\nClient disconnected:', reason);
    process.exit(1);
});

client.on('change_state', state => {
    console.log('STATE:', state);
});

client.on('authenticated', () => {
    console.log('AUTHENTICATED');
});

client.on('ready', () => {
    console.log('READY');
});

client.on('disconnected', reason => {
    console.log('DISCONNECTED:', reason);
});

client.on('loading_screen', (percent, msg) => {
    console.log('LOADING:', percent, msg);
});

// --------------------------------------------------------------------------
// Main logic
// --------------------------------------------------------------------------
async function runDownloadJob() {
    console.log('\n\nWhatsApp usable.\n');
    console.log('  Contact : ' + CONTACT_NAME);
    console.log('  Output  : ' + OUTPUT_DIR + '\n');

    try {
        // Find the chat -------------------------------------------------------
        const chats = await client.getChats();

        let chat = chats.find(c => c.name === CONTACT_NAME);
        if (!chat) {
            const lower = CONTACT_NAME.toLowerCase();
            chat = chats.find(c => c.name && c.name.toLowerCase().includes(lower));
        }

        if (!chat) {
            console.error('No chat found matching "' + CONTACT_NAME + '".');
            console.error('\nAvailable chats (first 20):');
            chats.slice(0, 20).forEach(c => console.error('  - ' + c.name));
            process.exit(1);
        }

        console.log('Found chat: "' + chat.name + '"\n');

        const messages = await chat.fetchMessages({ limit: 20 });

        let targetMessage = null;

        for (let i = messages.length - 1; i >= 0; i--) {
            const msg = messages[i];

            const isImg =
                msg.type === 'image' ||
                (msg.hasMedia &&
                    msg.mimetype &&
                    msg.mimetype.startsWith('image/'));

            if (isImg) {
                targetMessage = msg;
                break;
            }
        }

        if (!targetMessage) {
            console.error(
                'No image messages found in the last 20 messages of this chat.'
            );
            process.exit(1);
        }

        const targetTime = targetMessage.timestamp;
        const TIME_WINDOW_SEC = 60;

        const imageMsgs = messages.filter(msg => {
            const isImg =
                msg.type === 'image' ||
                (msg.hasMedia &&
                    msg.mimetype &&
                    msg.mimetype.startsWith('image/'));

            const inWindow =
                Math.abs(msg.timestamp - targetTime) <= TIME_WINDOW_SEC;

            return isImg && inWindow;
        });

        console.log(
            'Found ' + imageMsgs.length + ' image(s) to download.\n'
        );

        let savedCount = 0;
        let errorCount = 0;

        for (let i = 0; i < imageMsgs.length; i++) {
            const msg = imageMsgs[i];

            process.stdout.write(
                '  [' +
                (i + 1) +
                '/' +
                imageMsgs.length +
                '] Downloading... '
            );

            try {
                const media = await msg.downloadMedia();

                if (!media || !media.data) {
                    console.log('skipped (no data)');
                    errorCount++;
                    continue;
                }

                const ext = (media.mimetype || 'image/jpeg')
                    .split('/')[1]
                    .split(';')[0]
                    .replace('jpeg', 'jpg');

                const baseName = media.filename
                    ? path.basename(
                        media.filename,
                        path.extname(media.filename)
                    )
                    : (
                        timestamp() +
                        '_' +
                        String(i + 1).padStart(3, '0')
                    );

                const filename = baseName + '.' + ext;
                const filepath = path.join(OUTPUT_DIR, filename);

                fs.writeFileSync(
                    filepath,
                    Buffer.from(media.data, 'base64')
                );

                const sizeKB = (
                    fs.statSync(filepath).size / 1024
                ).toFixed(0);

                console.log(
                    'saved -> ' +
                    filename +
                    ' (' +
                    sizeKB +
                    ' KB)'
                );

                savedCount++;
            }
            catch (err) {
                console.log('failed (' + err.message + ')');
                errorCount++;
            }
        }

        console.log('\n------------------------------------------');

        if (savedCount > 0) {
            console.log(
                'Done! Saved ' +
                savedCount +
                ' image(s) to:'
            );

            console.log('  ' + OUTPUT_DIR);
        } else {
            console.log('No images were saved.');
        }

        if (errorCount > 0) {
            console.log(
                '(' +
                errorCount +
                ' skipped -- may have expired on WhatsApp servers)'
            );
        }

        console.log(
            '------------------------------------------\n'
        );
    }
    catch (err) {
        console.error('Unexpected error:', err.message);

        if (err.stack) {
            console.error(err.stack);
        }

        process.exit(1);
    }
    finally {
        await client.destroy();
        process.exit(0);
    }
}

// --------------------------------------------------------------------------
// Start
// --------------------------------------------------------------------------
let started = false;

async function waitUntilUsable() {
    while (!started) {
        try {
            const state = await client.getState();

            if (state === 'CONNECTED') {
                const chats = await client.getChats();

                if (
                    Array.isArray(chats) &&
                    chats.length > 0
                ) {
                    started = true;

                    console.log('\nClient usable.');
                    console.log(
                        'Connected chats: ' + chats.length + '\n'
                    );

                    await runDownloadJob();
                    return;
                }
            }
        }
        catch (_) {
            // Ignore startup race conditions
        }

        await new Promise(resolve =>
            setTimeout(resolve, 1000)
        );
    }
}

console.log('Starting WhatsApp client...');
console.log('(Takes ~10 seconds on first load)\n');

client.initialize();
waitUntilUsable();
