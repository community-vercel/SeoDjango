
                const puppeteer = require('puppeteer');
                const args = process.argv.slice(2);

                (async () => {
                    const browser = await puppeteer.launch({
                        args: ['--no-sandbox', '--disable-setuid-sandbox']
                    });
                    const page = await browser.newPage();
                    const url = args[0];

                    await page.goto(url, { waitUntil: 'networkidle0', timeout: 70000 });  // Wait for DOMContentLoaded only
                    await browser.close();
                })();
            