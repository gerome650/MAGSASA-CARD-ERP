"""
Image Upload Routes for AgSense ERP Product Catalog
Simplified version without Pillow dependency for deployment compatibility
"""

import os
import uuid

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

image_bp = Blueprint("image", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@image_bp.route("/api/upload-product-image", methods=["POST"])
def upload_product_image():
    """Upload product image with basic processing"""
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image file provided"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid file type. Please use JPG, PNG, or WebP",
                    }
                ),
                400,
            )

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return (
                jsonify(
                    {"success": False, "error": "File too large. Maximum size is 10MB"}
                ),
                400,
            )

        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"

        # Create directories if they don't exist
        upload_dir = os.path.join("src", "static", "images", "products")
        thumbnail_dir = os.path.join("src", "static", "images", "thumbnails")

        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(thumbnail_dir, exist_ok=True)

        # Save original image
        image_path = os.path.join(upload_dir, unique_filename)
        file.save(image_path)

        # For now, use the same image as thumbnail (simplified approach)
        thumbnail_path = os.path.join(thumbnail_dir, unique_filename)
        file.seek(0)
        with open(thumbnail_path, "wb") as thumb_file:
            thumb_file.write(file.read())

        # Return URLs relative to static folder
        image_url = f"/images/products/{unique_filename}"
        thumbnail_url = f"/images/thumbnails/{unique_filename}"

        return jsonify(
            {
                "success": True,
                "image_url": image_url,
                "thumbnail_url": thumbnail_url,
                "filename": unique_filename,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@image_bp.route("/api/delete-product-image", methods=["DELETE"])
def delete_product_image():
    """Delete product image files"""
    try:
        data = request.get_json()
        filename = data.get("filename")

        if not filename:
            return jsonify({"success": False, "error": "No filename provided"}), 400

        # Delete both original and thumbnail
        image_path = os.path.join("src", "static", "images", "products", filename)
        thumbnail_path = os.path.join("src", "static", "images", "thumbnails", filename)

        if os.path.exists(image_path):
            os.remove(image_path)

        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        return jsonify({"success": True, "message": "Image deleted successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
