# Konvertira frontend

Production-oriented React frontend for [konvertira.com](https://konvertira.com), a privacy-first image conversion and metadata cleaning service.

## Local image processing

JPG/JPEG, PNG, and static WEBP conversion and metadata removal run entirely in the browser. These operations do not call the backend API or upload image bytes.

The local workflow is:

1. The browser decodes the selected image with `createImageBitmap` or an image-element fallback.
2. Decoded pixels are rendered to a temporary canvas.
3. The canvas creates a new JPG, PNG, or WEBP blob without intentionally copying source metadata.
4. The browser downloads that blob through a temporary object URL, which is then revoked.

Canvas re-encoding may change compression and ICC/color-profile details. It does not guarantee removal of every conceivable privacy artifact. Animated WEBP is rejected because canvas processing would preserve only one frame. Transparent pixels are filled with white when producing JPEG.

## Requirements

- Node.js 22 or newer
- npm 10 or newer
- Docker (optional, for container builds)

## Local development

```bash
npm install
cp .env.example .env.local
npm run dev
```

On Windows PowerShell, copy the environment file with:

```powershell
Copy-Item .env.example .env.local
```

Vite prints the local URL when the development server starts (normally `http://localhost:5173`).

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Yes | Base URL of the Konvertira processing API, without a trailing slash. |
| `VITE_LOCAL_IMAGE_MAX_SIZE_MB` | No | Browser-processing compressed-file limit; defaults to `50`. |
| `VITE_LOCAL_IMAGE_MAX_PIXELS` | No | Browser-processing decoded pixel limit; defaults to `40000000`. |

Start from `.env.example`:

```env
VITE_API_BASE_URL=https://api.konvertira.com
VITE_LOCAL_IMAGE_MAX_SIZE_MB=50
VITE_LOCAL_IMAGE_MAX_PIXELS=40000000
```

Vite variables are embedded into the static bundle at build time. Changing this value in production requires rebuilding the frontend. Do not put API secrets in `VITE_*` variables because they are visible to users.

## API contract

The typed client in `src/services/api.ts` remains available for future PDFs, office documents, unsupported browser formats, and explicitly selected server workflows. Current JPG, PNG, and WEBP operations use `src/services/localImageProcessor.ts` and do not call these endpoints.

The server client expects these endpoints when used:

- `POST /images/remove-metadata` — `multipart/form-data` with a `file` field.
- `POST /images/convert` — `multipart/form-data` with `file` and `format` (`jpg`, `png`, or `webp`) fields.

Successful responses should contain the processed file as the response body. A `Content-Disposition` response header with a filename is supported and recommended. Errors may be JSON with a `message` or `detail` string, or plain text. The API must allow requests from the frontend origin using appropriate CORS headers.

## Checks and production build

```bash
npm run typecheck
npm test
npm run build
npm run preview
```

The production output is written to `dist/`.

## Docker

Build with the public API URL baked into the Vite bundle:

```bash
docker build --build-arg VITE_API_BASE_URL=https://api.konvertira.com -t konvertira-frontend .
```

Run the container:

```bash
docker run --rm -p 8080:80 konvertira-frontend
```

Open `http://localhost:8080`. The container exposes port 80 and serves the app with nginx. The nginx fallback configuration sends unknown application paths to `index.html`, so direct visits to `/privacy`, `/terms`, and `/about` work correctly.

## Deployment notes

- Configure HTTPS at the load balancer, reverse proxy, or hosting platform.
- Pass the correct `VITE_API_BASE_URL` during every environment-specific image build.
- Configure the API's CORS allowlist for the deployed frontend origin.
- Review the Privacy and Terms pages when processing behavior or applicable legal requirements change.
- Keep public repository links pointed to `https://github.com/bijesnopile/konvertira`.
- The frontend does not include authentication, payments, analytics, or backend processing logic.
