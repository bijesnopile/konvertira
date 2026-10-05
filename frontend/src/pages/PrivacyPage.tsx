import { PageIntro } from '../components/PageIntro'
import { ProcessingModeInfo } from '../components/ProcessingMode'

export function PrivacyPage() {
  return (
    <>
      <PageIntro eyebrow="Privacy" title="A local-first approach to your files.">
        Clear information about what stays in your browser, what may use a server, and why.
      </PageIntro>

      <article className="legal-content">
        <p className="text-sm text-slate-500">Last updated: October 5, 2026</p>

        <h2>1. Privacy philosophy</h2>
        <p>Konvertira is a small independent side project built by a student and solo developer around a simple idea: basic file conversion should be useful, accessible, and respectful of your privacy. It should not require an unnecessary subscription or account.</p>
        <p>Whenever an operation can work reliably in the browser, Konvertira prefers local processing. Some tools need server infrastructure, so the interface is designed to distinguish those workflows clearly.</p>

        <div className="my-10 grid gap-4 sm:grid-cols-2">
          <ProcessingModeInfo
            mode="local"
            title="Supported image tools"
            description="JPG, PNG, and static WEBP conversion and metadata removal run directly in your browser."
          />
          <ProcessingModeInfo
            mode="server"
            title="Some other tools"
            description="Documents, unsupported formats, and MCP workflows may require a clearly indicated temporary upload."
          />
        </div>

        <h2>2. Images processed in your browser</h2>
        <p>For supported JPG, PNG, and WEBP image tools, your browser does the work. The selected image is not sent to Konvertira or to the Konvertira API.</p>
        <p>Your browser decodes the image, renders its visible pixels to a temporary canvas, and creates a new image file locally. The result is generated and downloaded on your device. Server infrastructure is not involved in this workflow.</p>

        <h2>3. Metadata removal</h2>
        <p>Images may contain GPS or location data, EXIF fields, camera information, capture dates, software information, embedded comments, and related details.</p>
        <p>Konvertira’s local cleaning process is designed to remove common embedded image metadata by creating a new image from decoded pixels instead of copying the original file container. Original metadata is not intentionally carried into the result.</p>
        <p>This is not a guarantee that every conceivable privacy artifact is removed. Browser re-encoding can also change compression, color profiles, animation, and other format-specific properties. Animated WEBP images are currently rejected by the local tool.</p>

        <h2>4. When a file may need to be uploaded</h2>
        <p>Some operations cannot reasonably or reliably run entirely in a browser. PDF tools, Office or document conversion, unsupported formats, and MCP or ChatGPT workflows may require server processing.</p>
        <p>When you explicitly use a server-backed tool, including Konvertira through ChatGPT, the file may be transferred to or retrieved by Konvertira's server for temporary processing. The file is processed only for the requested operation, and temporary files may exist while processing and download are required.</p>
        <p>Konvertira does not silently upload an image when local processing fails. The current image tool shows an error and keeps the file on your device.</p>

        <h2>5. Temporary storage</h2>
        <p>Files processed on the server may be stored temporarily so the requested operation can be completed and the result downloaded. Temporary processed files are currently configured to be removed after approximately 15 minutes.</p>
        <p>This describes Konvertira’s configured application storage. It does not claim immediate deletion from every cache, backup, or underlying infrastructure system.</p>

        <h2>6. Accounts and necessary data</h2>
        <p>The basic website image tools do not require an account. Because those image operations are local, Konvertira does not need to receive the image contents.</p>
        <p>For server-backed features, limited technical request information and operational logs may be handled as reasonably necessary to deliver, protect, and troubleshoot the service.</p>

        <h2>7. An independent project with practical limits</h2>
        <p>Konvertira is independently operated, so server capacity is limited. File-size limits, processing limits, and format restrictions may apply, especially to server-side tools.</p>
        <p>Local browser processing reduces infrastructure costs and avoids sending every supported image through a server. The goal is to improve capacity and supported formats over time without making promises about specific release dates.</p>

        <h2>8. Security</h2>
        <p>HTTPS is used for communication with Konvertira’s web services, and reasonable technical measures are used to operate the service safely. Local image processing reduces the need to transmit supported image files.</p>
        <p>No online or local software can promise perfect security or zero risk. Konvertira does not claim end-to-end encryption, zero-knowledge processing, or guaranteed anonymization.</p>

        <h2>9. Third-party infrastructure</h2>
        <p>Konvertira may rely on third-party services for hosting, DNS or content delivery, MCP-related functionality, and other operational infrastructure. When a server-backed feature is used, those providers may handle limited data as necessary to provide their infrastructure.</p>

        <h2>10. Changes to the service</h2>
        <p>Konvertira is actively developed. Processing methods, supported formats, safety limits, and server behavior may change as the project improves. This page will be updated when important privacy-related behavior changes.</p>

        <h2>11. Contact</h2>
        <p>Questions about privacy or file handling can be sent to <a href="mailto:legal@konvertira.com">legal@konvertira.com</a>.</p>
      </article>
    </>
  )
}
