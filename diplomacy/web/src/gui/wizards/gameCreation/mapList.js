class VariantInfo {
    constructor(variantName, variantTitle) {
        this.name = variantName;
        this.title = variantTitle;
        this.map = null;
    }

    svgName() {
        return this.map.name;
    }
}

class MapInfo {
    constructor(mapName, mapTitle, variants) {
        this.name = mapName;
        this.title = mapTitle;
        this.variants = null;
        if (variants) {
            this.variants = [];
            for (let variant of variants) {
                variant.map = this;
                this.variants.push(variant);
            }
        }
    }

    svgName() {
        return this.name;
    }
}

export const Maps = [
    new MapInfo('standard', 'Standard', [
        new VariantInfo('standard', 'Default'),
        new VariantInfo('standard_age_of_empires', 'Age of empires'),
        new VariantInfo('standard_age_of_empires_2', 'Age of empires II'),
        new VariantInfo('standard_fleet_rome', 'Fleet at Rome'),
        new VariantInfo('standard_france_austria', 'France VS Austria'),
        new VariantInfo('standard_germany_italy', 'Germany VS Italy')
    ]),
];
