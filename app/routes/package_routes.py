from flask import Blueprint, jsonify, request
from app.services.package_service import PackageService

from ..auth import jwt_required
from ..errors.not_found_error import NotFoundError

package_bp = Blueprint('package_bp', __name__)

@package_bp.route('/packages', methods=['POST'])
@jwt_required(pass_payload=False)
def add_package():
    data = request.json
    try:
        # Gerekli alanları kontrol ediyoruz ve eksikse uygun hata mesajı döndürüyoruz
        required_fields = ["title", "monthly_original_price", "yearly_original_price", "features", "credits"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"message": f"Missing required field: {field}"}), 400

        package_id = PackageService.add_package(data)
        return jsonify({"message": "Package added successfully", "package_id": str(package_id)}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@package_bp.route('/packages', methods=['GET'])
@jwt_required(pass_payload=False)
def get_packages():
    packages = PackageService.get_all_packages()
    return jsonify(packages), 200

@package_bp.route('/packages/<package_id>', methods=['GET'])
@jwt_required(pass_payload=False)
def get_package(package_id):
    try:
        package = PackageService.get_package_by_id(package_id)
        return jsonify(package), 200
    except ValueError:
        return jsonify({"message": "Package not found"}), 404

@package_bp.route('/packages/<package_id>', methods=['PUT'])
@jwt_required(pass_payload=False)
def update_package(package_id):
    data = request.json
    try:
        # Gerekli alanları kontrol ediyoruz ve eksikse uygun hata mesajı döndürüyoruz
        required_fields = ["title", "monthly_original_price", "yearly_original_price", "features"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"message": f"Missing required field: {field}"}), 400

        PackageService.update_package(package_id, data)
        return jsonify({"message": "Package updated successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except NotFoundError:
        return jsonify({"message": "Package not found"}), 404

@package_bp.route('/packages/<package_id>', methods=['DELETE'])
@jwt_required(pass_payload=False)
def delete_package(package_id):
    try:
        if PackageService.delete_package(package_id):
            return jsonify({"message": "Package deleted successfully"}), 200
        else:
            return jsonify({"message": "Package not found"}), 404
    except NotFoundError:
        return jsonify({"message": "Package not found"}), 404
