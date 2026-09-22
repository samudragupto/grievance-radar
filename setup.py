from setuptools import find_packages, setup

setup(
    name="grievance-radar",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=3.1.0",
        "Flask-SQLAlchemy>=3.1.1",
        "sentence-transformers>=3.0.0",
        "scikit-learn>=1.5.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "pandas>=2.0.0",
        "reportlab>=4.2.0",
        "python-dotenv>=1.0.0",
        "gunicorn>=22.0.0",
    ],
)
