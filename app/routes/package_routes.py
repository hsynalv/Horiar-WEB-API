from flask import Blueprint, jsonify, request
from app.services.package import PackageService

package_bp = Blueprint('package', __name__)

@package_bp.route('/packages', methods=['POST'])
def add_package():
    data = request.json
    try:
        package_id = PackageService.add_package(data)
        return jsonify({"message": "Package added successfully", "package_id": str(package_id)}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@package_bp.route('/packages', methods=['GET'])
def get_packages():
    packages = PackageService.get_all_packages()
    return jsonify(packages), 200

@package_bp.route('/packages/<package_id>', methods=['GET'])
def get_package(package_id):
    package = PackageService.get_package_by_id(package_id)
    if package:
        return jsonify(package), 200
    else:
        return jsonify({"message": "Package not found"}), 404

@package_bp.route('/packages/<package_id>', methods=['PUT'])
def update_package(package_id):
    data = request.json
    try:
        if not PackageService.get_package_by_id(package_id):
            return jsonify({"message": "Package not found"}), 404

        PackageService.update_package(package_id, data)
        return jsonify({"message": "Package updated successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@package_bp.route('/packages/<package_id>', methods=['DELETE'])
def delete_package(package_id):
    if not PackageService.delete_package(package_id):
        return jsonify({"message": "Package not found"}), 404

    return jsonify({"message": "Package deleted successfully"}), 200
