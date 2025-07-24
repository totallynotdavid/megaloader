import os
import megaloader

# Bunkr URLs:
# - Album URL:    https://bunkrr.su/a/pSbD1FmM
# - Single File:  https://bunkrr.su/d/megaloader-main-RKEICuly.zip
#                 https://bunkr.si/f/StoRbcXsF0Yje

# Pixeldrain URLs:
# - Single File:  https://pixeldrain.com/u/95u1wnsd
# - List:         https://pixeldrain.com/l/nH4ZKt3b

BUNKR_TEST_URL = "https://bunkrr.su/a/pSbD1FmM"
PIXELDRAIN_TEST_URL = "https://pixeldrain.com/l/nH4ZKt3b"
OUTPUT_DIR = "./downloads"


def main():
    output_path = os.path.abspath(OUTPUT_DIR)
    print(f"[EXAMPLE] Files will be downloaded to: {output_path}")
    os.makedirs(output_path, exist_ok=True)

    print("\n--- Example 1: Auto-Detect and download (Bunkr) ---")
    bunkr_url = BUNKR_TEST_URL
    success_bunkr = megaloader.download(bunkr_url, output_path)
    if success_bunkr:
        print(
            "[EXAMPLE] Bunkr download process completed (check for individual file successes)."
        )
    else:
        print("[EXAMPLE] Bunkr download process failed.")

    print("\n--- Example 2: Auto-Detect and download (PixelDrain) ---")
    pixeldrain_url = PIXELDRAIN_TEST_URL
    success_pd = megaloader.download(pixeldrain_url, output_path)
    if success_pd:
        print(
            "[EXAMPLE] PixelDrain download process completed (check for individual file successes)."
        )
    else:
        print("[EXAMPLE] PixelDrain download process failed.")

    print("\n--- Example 3: Direct plugin usage (Bunkr) ---")
    # 1. Instantiate the specific plugin
    bunkr_plugin = megaloader.Bunkr(bunkr_url)

    print(f"[EXAMPLE] Exporting items from {bunkr_url}...")
    exported_items = list(bunkr_plugin.export())
    print(f"[EXAMPLE] Found {len(exported_items)} items to process.")

    # 3. Iterate and download each item
    if exported_items:
        plugin_output_dir = os.path.join(output_path, "bunkr_direct_plugin")
        os.makedirs(plugin_output_dir, exist_ok=True)

        for i, file_page_url in enumerate(
            exported_items[:2], 1
        ):  # Download first 2 for demo
            print(f"[EXAMPLE] [Direct Plugin] Downloading item {i}...")
            # The plugin's download_file handles the specifics for that service
            result_path = bunkr_plugin.download_file(file_page_url, plugin_output_dir)
            if result_path:
                print(
                    f"[EXAMPLE] [Direct Plugin] Successfully downloaded to: {result_path}"
                )
            else:
                print(f"[EXAMPLE] [Direct Plugin] Failed to download item {i}.")

    print("\n[EXAMPLE] All examples finished. Check the output directory.")


if __name__ == "__main__":
    main()
