// Placeholder descriptions for dishes without descriptions
// These are realistic Swedish lunch descriptions

export const placeholderDescriptions: { [key: string]: string } = {
  // Asian dishes
  "Orange Chicken & Thai Tofu": "Krispig kyckling i sötsur apelsinsås med färska grönsaker och jasminris",
  "Thai Green Curry": "Kycklingfilé i grön curry med kokosmjölk, bambuskott och thaibasilika",
  "Pad Thai": "Wokade risnudlar med räkor, tofu, jordnötter och lime",
  "Thai Red Curry": "Röd curry med kyckling, aubergine och thailändska grönsaker",
  
  // Swedish classics
  "Köttbullar": "Klassiska svenska köttbullar med gräddsås, lingonsylt och potatismos",
  "Pannbiff": "Saftig pannbiff med lök, brunsås och kokt potatis",
  "Fiskgratäng": "Gratinerad fisk med räkor, dillsås och potatismos",
  "Kalops": "Traditionell kalops med rödbetor, morötter och kokt potatis",
  "Pytt i panna": "Stekt pytt i panna med rödbetor och stekt ägg",
  
  // Burgers & Grills
  "Cheeseburger": "Saftig högrevsburgare med cheddar, sallad, tomat och pickles",
  "Bacon Burger": "Grillad burgare med bacon, ost och BBQ-sås",
  "Veggie Burger": "Vegetarisk burgare med halloumi, avokado och aioli",
  "Grilled Chicken": "Grillad kycklingfilé med örtsmör och säsongens grönsaker",
  
  // Pasta dishes
  "Pasta Carbonara": "Krämig carbonara med bacon, parmesan och svartpeppar",
  "Pasta Bolognese": "Klassisk köttfärssås med tomat, vitlök och färska örter",
  "Pasta Arrabiata": "Pikant tomatsås med chili, vitlök och persilja",
  "Lasagne": "Hemlagad lasagne med köttfärssås, bechamel och gratinerad ost",
  
  // Fish dishes
  "Lax": "Ugnsbakad lax med dillsås, citron och kokt potatis",
  "Torsk": "Panerad torskfilé med remouladsås och potatismos",
  "Räkor": "Handskalade räkor med aioli, bröd och sallad",
  
  // Vegetarian/Vegan
  "Falafel": "Friterade kikärtsbollar med hummus, tahini och pitabröd",
  "Vegetarisk Lasagne": "Lasagne med spenat, ricotta och tomatsås",
  "Vegan Bowl": "Quinoa med rostade grönsaker, avokado och tahindressing",
  "Halloumi": "Grillad halloumi med couscous och myntayoghurt",
  
  // Soups
  "Ärtsoppa": "Traditionell ärtsoppa med fläsk, senap och tunna pannkakor",
  "Fisksoppa": "Krämig fisksoppa med räkor, dill och aioli",
  "Tomatsoppa": "Hemlagad tomatsoppa med basilika och krutonger",
  
  // Salads
  "Caesar Sallad": "Romansallad med kyckling, parmesan, krutonger och caesardressing",
  "Grekisk Sallad": "Fetaost, oliver, tomat, gurka och rödlök med oregano",
  "Räksallad": "Handskalade räkor på bädd av mixsallad med Rhode Island-dressing",
  
  // Pizza
  "Margherita": "Tomatsås, mozzarella och färsk basilika",
  "Vesuvio": "Tomatsås, mozzarella och skinka",
  "Capricciosa": "Tomatsås, mozzarella, skinka och champinjoner",
  "Quattro Formaggi": "Fyra ostar: mozzarella, gorgonzola, parmesan och pecorino",
  
  // Persian/Middle Eastern
  "Kebab": "Grillat lamm- eller kycklingkött med ris, grillad tomat och yoghurtsås",
  "Koobideh": "Två spett med kryddad färs, serveras med saffransris",
  "Gheyme bademjoon": "Lammkött med gula linser, stekt aubergine och saffransris",
  "Ghormeh Sabzi": "Persisk örtgryta med lamm, bönor och lime",
  
  // Indian
  "Chicken Tikka Masala": "Tandoori-kyckling i krämig tomatsås med garam masala",
  "Palak Paneer": "Indisk ost i krämig spenatsås med vitlök och ingefära",
  "Butter Chicken": "Marinerad kyckling i mild tomat- och smörsås",
  
  // Thai specific
  "Pad Krapow": "Wokad färs med thaibasilika, chili och stekt ägg",
  "Tom Yum": "Stark och syrlig soppa med räkor, citrongräs och koriander",
  "Massaman Curry": "Mild curry med nötkött, potatis och jordnötter",
  
  // Mexican/Tex-Mex
  "Tacos": "Mjuka tortillas med kryddat kött, sallad, ost och salsa",
  "Quesadilla": "Gratinerad tortilla fylld med kyckling, ost och grönsaker",
  "Burrito": "Stor tortilla fylld med ris, bönor, kött och grönsaker",
  
  // Default/Generic
  "Dagens Special": "Kockens val med säsongens ingredienser",
  "Veckans Rätt": "Specialkomponerad rätt med utvalda råvaror",
  "Husmanskost": "Traditionell svensk husmanskost tillagad med omsorg"
};

// Function to get description for a dish
export function getPlaceholderDescription(dishName: string): string {
  // Try exact match first
  if (placeholderDescriptions[dishName]) {
    return placeholderDescriptions[dishName];
  }
  
  // Try partial matches
  const lowerName = dishName.toLowerCase();
  
  // Check for common keywords
  for (const [key, value] of Object.entries(placeholderDescriptions)) {
    if (lowerName.includes(key.toLowerCase())) {
      return value;
    }
  }
  
  // Category-based fallbacks
  if (lowerName.includes('burger')) {
    return "Saftig burgare med färska grönsaker och pommes frites";
  }
  if (lowerName.includes('pasta')) {
    return "Al dente-kokt pasta med husets specialsås";
  }
  if (lowerName.includes('sallad') || lowerName.includes('salad')) {
    return "Färsk sallad med säsongens grönsaker och dressing";
  }
  if (lowerName.includes('soppa') || lowerName.includes('soup')) {
    return "Varm soppa serverad med bröd och smör";
  }
  if (lowerName.includes('fisk') || lowerName.includes('fish')) {
    return "Dagens färska fisk med tillbehör";
  }
  if (lowerName.includes('kyckling') || lowerName.includes('chicken')) {
    return "Grillad eller stekt kyckling med säsongens tillbehör";
  }
  if (lowerName.includes('vegetarisk') || lowerName.includes('vegan')) {
    return "Näringsrik vegetarisk rätt med färska grönsaker";
  }
  if (lowerName.includes('curry')) {
    return "Aromatisk curry med ris och naan-bröd";
  }
  if (lowerName.includes('wok')) {
    return "Wokade grönsaker och protein med asiatiska smaker";
  }
  
  // Ultimate fallback
  return "Klassisk lunchrätt tillagad med färska ingredienser";
}