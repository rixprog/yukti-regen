import os
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()
# Make sure your Gemini client is initialized
# Example:
from google.genai import Client
client = Client()

def main():
    print("=== AI Image Editor (Terminal Version) ===\n")

    while True:
        # Ask user for inputs
        image_path = input("Enter the path to the image (or type 'exit' to quit): ").strip()
        if image_path.lower() == "exit":
            print("Exiting...")
            break

        prompt = input("Enter your prompt for editing: ").strip()
        if not prompt:
            print("❌ Prompt cannot be empty. Try again.\n")
            continue

        # Check if file exists
        if not os.path.exists(image_path):
            print("❌ Error: Image not found at the given path.\n")
            continue

        # Create before/ and after/ directories
        os.makedirs("before", exist_ok=True)
        os.makedirs("after", exist_ok=True)

        # Save original image to "before" folder
        before_image = Image.open(image_path)
        before_save_path = os.path.join("before", os.path.basename(image_path))
        before_image.save(before_save_path)
        print(f"✅ Original image saved to: {before_save_path}")

        # Call Gemini model with prompt + image
        print("⏳ Generating edited image(s)...")
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[prompt, before_image],
            )
        except Exception as e:
            print(f"❌ Error during image generation: {e}\n")
            continue

        # Extract and save generated images
        count = 0
        for idx, part in enumerate(response.candidates[0].content.parts, start=1):
            if part.inline_data is not None:
                img = Image.open(BytesIO(part.inline_data.data))
                after_path = os.path.join("after", f"after_{idx}.jpg")
                img.save(after_path)
                print(f"✨ Edited image saved to: {after_path}")
                count += 1

        if count == 0:
            print("⚠ No images were generated.\n")
        else:
            print(f"✅ Finished! {count} image(s) saved in 'after/' folder.\n")

if __name__ == "__main__":
    main()