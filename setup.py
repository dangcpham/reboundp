import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="reboundp",
    version="0.0.4",
    author="Dang Pham",
    author_email="dang.pham@astro.utoronto.ca",
    description="A package for managing parallelized Python-based REBOUND instances",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dangcpham/reboundp",
    project_urls={
        "Bug Tracker": "https://github.com/dangcpham/reboundp/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=["joblib"],
    extras_require = {
        "port": ["rebound>=4.0.0", "urllib3"],
        "dashboard":  ["rebound>=4.0.0", "urllib3", "flask"]
    }
)