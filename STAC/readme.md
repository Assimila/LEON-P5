# LEON P5 STAC

In this directory we create a STAC catalogue for the LEON P5 ouput experimental dataset,
for inclusion in the ESA Project Results Repository (PRR).

PRR requires:

- A STAC collection according to [APEx Data Provider Guidelines](https://esa-apex.github.io/apex_documentation/interoperability/datahosting.html)
- Which must also pass [PRR Collections Specifications](https://eoresults.esa.int/prr_collection_specifications.html)
- And is validated by https://eoresults.esa.int/prr_collection_editor.html

For this pilot, the output dataset is small enough to be held locally,
so that we can build the STAC in a neighbouring directory.

```bash
$ tree
.
├── STAC
│   ├── catalog.json
│   ├── BII
│   │   ├── collection.json
│   │   ├── thumbnail.jpg
│   │   └── items/
│   │       ├── <item-id>.json
│   │       └── ...
│   └── LUI
│       ├── collection.json
│       ├── thumbnail.jpg
│       └── items/
│           ├── <item-id>.json
│           └── ...
├── data
│   ├── BII
│   │   └── ...
│   └── LUI
│       └── ...
├── descriptions
│   ├── BII.md
│   └── LUI.md
├── thumbnails
│   ├── BII.jpg
│   └── LUI.jpg
├── environment.yml
├── readme.md
└── stac-ify.py
```

# create conda environment

```bash
cd STAC
conda env create -f environment.yml
```

make sure to activate the environment

```bash
conda activate LEON-P5-STAC
```

update the environment

```bash
conda env update -f environment.yml
```
