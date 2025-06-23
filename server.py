from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route("/resolve", methods=["GET"])
def resolve_stream():
    channel_url = request.args.get("channelUrl")
    token = request.args.get("token")

    if not channel_url or not token:
        return jsonify({"success": False, "error": "Missing channelUrl or token"}), 400

    back_url = "vrplay://back/channel/0"
    auth_url = f"https://www.ottplay.com/auth?seoUrl={channel_url}&token={token}&backUrl={back_url}&source=SDTECHNOLOGIES&appName=VRPLAY"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        stream_url = None

        def handle_request(route, req):
            nonlocal stream_url
            url = req.url
            if ".m3u8" in url and not stream_url:
                stream_url = url.replace("/0.m3u8", "/3.m3u8").replace("/1.m3u8", "/3.m3u8")
            route.continue_()

        page.route("**/*", handle_request)

        try:
            page.goto(auth_url, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(10000)  # wait for JavaScript redirect
        except Exception as e:
            print("Error:", str(e))
            browser.close()
            return jsonify({"success": False, "error": str(e)}), 500

        browser.close()

        if stream_url:
            return jsonify({"success": True, "url": stream_url})
        else:
            return jsonify({"success": False, "error": "Stream URL not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
