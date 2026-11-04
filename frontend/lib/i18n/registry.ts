/* Universal Global Language Selector — language registry.
 *
 * Every entry carries an ISO 639 identifier and a BCP 47 locale tag.
 * `status` distinguishes selector availability from translation
 * completeness: 'translated' (full dictionary), 'partial'
 * (representative namespaces, machine-drafted, human review pending),
 * 'unavailable' (no dictionary; hidden from the selector until
 * translations ship — legacy persisted tags still fall back to
 * English with an explicit note, never wrong-language text).
 * Regional variants resolve through BCP 47 fallback (tag -> base).
 */

export type TranslationStatus = "translated" | "partial" | "unavailable";

/* localStorage key for the persisted visitor preference. */
export const LOCALE_STORAGE_KEY = "cruiseshield-locale";

export interface LanguageEntry {
  /** BCP 47 locale tag, e.g. "pt-BR", "zh-Hans". */
  tag: string;
  /** ISO 639-1, -2 or -3 identifier, e.g. "pt", "chr". */
  iso: string;
  /** Native endonym in its own script. */
  native: string;
  /** English exonym for search/discovery. */
  english: string;
  /** Broad language family for grouped discovery. */
  family: string;
  /** Right-to-left script. */
  rtl: boolean;
  /** Translation completeness (see above). */
  status: TranslationStatus;
}

/* [tag, iso, native, english, family, rtl] — status derives below:
 * en (+en-GB/en-NG, same dictionary) translated; 11 partial
 * (ar/es/fr/ha/hi/ig/ja/pt/sw/yo/zh); everything else unavailable. */
const RAW: Array<[string, string, string, string, string, boolean]> = [
  ["aa", "aa", "Afaraf", "Afar", "Afro-Asiatic", false],
  ["ab", "ab", "аҧсуа бызшәа", "Abkhaz", "Northwest Caucasian", false],
  ["ae", "ae", "avesta", "Avestan", "Indo-European", false],
  ["af", "af", "Afrikaans", "Afrikaans", "Indo-European", false],
  ["ak", "ak", "Akan", "Akan", "Niger-Congo", false],
  ["am", "am", "አማርኛ", "Amharic", "Afro-Asiatic", false],
  ["am-Ethi", "am", "አማርኛ (ኢትዮጵያ)", "Amharic (Ethiopic)", "Afro-Asiatic", false],
  ["an", "an", "aragonés", "Aragonese", "Indo-European", false],
  ["ar", "ar", "العربية", "Arabic", "Afro-Asiatic", true],
  ["ar-EG", "ar", "العربية (مصر)", "Arabic (Egypt)", "Afro-Asiatic", true],
  ["ar-SA", "ar", "العربية (السعودية)", "Arabic (Saudi Arabia)", "Afro-Asiatic", true],
  ["as", "as", "অসমীয়া", "Assamese", "Indo-European", false],
  ["av", "av", "авар мацӀ", "Avaric", "Northeast Caucasian", false],
  ["ay", "ay", "aymar aru", "Aymara", "Aymaran", false],
  ["az", "az", "azərbaycan dili", "Azerbaijani", "Turkic", false],
  ["az-Latn", "az", "azərbaycan dili (latın)", "Azerbaijani (Latin)", "Turkic", false],
  ["az-Arab", "az", "آذربایجان دیلی", "Azerbaijani (Arabic)", "Turkic", true],
  ["ba", "ba", "башҡорт теле", "Bashkir", "Turkic", false],
  ["be", "be", "беларуская", "Belarusian", "Indo-European", false],
  ["bg", "bg", "български", "Bulgarian", "Indo-European", false],
  ["bi", "bi", "Bislama", "Bislama", "Creole", false],
  ["bm", "bm", "bamanankan", "Bambara", "Mande", false],
  ["bn", "bn", "বাংলা", "Bengali", "Indo-European", false],
  ["bo", "bo", "བོད་སྐད་", "Tibetan", "Sino-Tibetan", false],
  ["br", "br", "brezhoneg", "Breton", "Indo-European", false],
  ["bs", "bs", "bosanski", "Bosnian", "Indo-European", false],
  ["ca", "ca", "català", "Catalan", "Indo-European", false],
  ["ce", "ce", "нохчийн мотт", "Chechen", "Northeast Caucasian", false],
  ["ch", "ch", "Chamoru", "Chamorro", "Austronesian", false],
  ["chr", "chr", "ᏣᎳᎩ", "Cherokee", "Iroquoian", false],
  ["co", "co", "corsu", "Corsican", "Indo-European", false],
  ["cr", "cr", "ᓀᐦᐃᔭᐍᐏᐣ", "Cree", "Algic", false],
  ["cs", "cs", "čeština", "Czech", "Indo-European", false],
  ["cu", "cu", "словѣньскъ", "Old Church Slavonic", "Indo-European", false],
  ["cv", "cv", "чӑваш чӗлхи", "Chuvash", "Turkic", false],
  ["cy", "cy", "Cymraeg", "Welsh", "Indo-European", false],
  ["da", "da", "dansk", "Danish", "Indo-European", false],
  ["de", "de", "Deutsch", "German", "Indo-European", false],
  ["dv", "dv", "ދިވެހި", "Dhivehi", "Indo-European", true],
  ["dz", "dz", "རྫོང་ཁ", "Dzongkha", "Sino-Tibetan", false],
  ["ee", "ee", "Eʋegbe", "Ewe", "Niger-Congo", false],
  ["efi", "efi", "Efik", "Efik", "Niger-Congo", false],
  ["el", "el", "Ελληνικά", "Greek", "Indo-European", false],
  ["en", "en", "English", "English", "Indo-European", false],
  ["en-GB", "en", "English (UK)", "English (United Kingdom)", "Indo-European", false],
  ["en-NG", "en", "English (Nigeria)", "English (Nigeria)", "Indo-European", false],
  ["eo", "eo", "Esperanto", "Esperanto", "Constructed", false],
  ["es", "es", "español", "Spanish", "Indo-European", false],
  ["es-MX", "es", "español (México)", "Spanish (Mexico)", "Indo-European", false],
  ["es-AR", "es", "español (Argentina)", "Spanish (Argentina)", "Indo-European", false],
  ["et", "et", "eesti", "Estonian", "Uralic", false],
  ["eu", "eu", "euskara", "Basque", "Isolate", false],
  ["fa", "fa", "فارسی", "Persian", "Indo-European", true],
  ["ff", "ff", "Fulfulde", "Fula", "Niger-Congo", false],
  ["fi", "fi", "suomi", "Finnish", "Uralic", false],
  ["fil", "fil", "Wikang Filipino", "Filipino", "Austronesian", false],
  ["fj", "fj", "Na Vosa Vakaviti", "Fijian", "Austronesian", false],
  ["fo", "fo", "føroyskt", "Faroese", "Indo-European", false],
  ["fon", "fon", "Fon", "Fon", "Niger-Congo", false],
  ["fr", "fr", "français", "French", "Indo-European", false],
  ["fr-CA", "fr", "français (Canada)", "French (Canada)", "Indo-European", false],
  ["fr-BE", "fr", "français (Belgique)", "French (Belgium)", "Indo-European", false],
  ["fy", "fy", "Frysk", "Western Frisian", "Indo-European", false],
  ["ga", "ga", "Gaeilge", "Irish", "Indo-European", false],
  ["gd", "gd", "Gàidhlig", "Scottish Gaelic", "Indo-European", false],
  ["gl", "gl", "galego", "Galician", "Indo-European", false],
  ["gn", "gn", "Avañe'ẽ", "Guarani", "Tupian", false],
  ["gu", "gu", "ગુજરાતી", "Gujarati", "Indo-European", false],
  ["gv", "gv", "Gaelg", "Manx", "Indo-European", false],
  ["ha", "ha", "Hausa", "Hausa", "Afro-Asiatic", false],
  ["ha-Latn", "ha", "Hausa (Latin)", "Hausa (Latin)", "Afro-Asiatic", false],
  ["ha-Arab", "ha", "هَرْشَن هَوْسَ", "Hausa (Ajami)", "Afro-Asiatic", true],
  ["haw", "haw", "ʻŌlelo Hawaiʻi", "Hawaiian", "Austronesian", false],
  ["he", "he", "עברית", "Hebrew", "Afro-Asiatic", true],
  ["hi", "hi", "हिन्दी", "Hindi", "Indo-European", false],
  ["ho", "ho", "Hiri Motu", "Hiri Motu", "Creole", false],
  ["hr", "hr", "hrvatski", "Croatian", "Indo-European", false],
  ["ht", "ht", "Kreyòl ayisyen", "Haitian Creole", "Creole", false],
  ["hu", "hu", "magyar", "Hungarian", "Uralic", false],
  ["hy", "hy", "Հայերեն", "Armenian", "Indo-European", false],
  ["hz", "hz", "Otjiherero", "Herero", "Niger-Congo", false],
  ["ia", "ia", "interlingua", "Interlingua", "Constructed", false],
  ["id", "id", "Bahasa Indonesia", "Indonesian", "Austronesian", false],
  ["ie", "ie", "Interlingue", "Interlingue", "Constructed", false],
  ["ig", "ig", "Igbo", "Igbo", "Niger-Congo", false],
  ["ii", "ii", "ꆈꌠ꒿", "Nuosu Yi", "Sino-Tibetan", false],
  ["ik", "ik", "Iñupiaq", "Inupiaq", "Eskimo-Aleut", false],
  ["io", "io", "Ido", "Ido", "Constructed", false],
  ["is", "is", "íslenska", "Icelandic", "Indo-European", false],
  ["it", "it", "italiano", "Italian", "Indo-European", false],
  ["iu", "iu", "ᐃᓄᒃᑑᑦ", "Inuktitut", "Eskimo-Aleut", false],
  ["ja", "ja", "日本語", "Japanese", "Japonic", false],
  ["jv", "jv", "basa Jawa", "Javanese", "Austronesian", false],
  ["ka", "ka", "ქართული", "Georgian", "Kartvelian", false],
  ["kg", "kg", "Kikongo", "Kongo", "Niger-Congo", false],
  ["ki", "ki", "Gĩkũyũ", "Kikuyu", "Niger-Congo", false],
  ["kj", "kj", "Oshikwanyama", "Kwanyama", "Niger-Congo", false],
  ["kk", "kk", "қазақша", "Kazakh", "Turkic", false],
  ["kl", "kl", "kalaallisut", "Greenlandic", "Eskimo-Aleut", false],
  ["km", "km", "ខ្មែរ", "Khmer", "Austroasiatic", false],
  ["kn", "kn", "ಕನ್ನಡ", "Kannada", "Dravidian", false],
  ["ko", "ko", "한국어", "Korean", "Koreanic", false],
  ["kr", "kr", "Kanuri", "Kanuri", "Nilo-Saharan", false],
  ["ks", "ks", "کٲشُر", "Kashmiri", "Indo-European", true],
  ["ku", "ku", "kurdî", "Kurdish", "Indo-European", false],
  ["ku-Latn", "ku", "kurdî (latînî)", "Kurdish (Latin)", "Indo-European", false],
  ["ku-Arab", "ku", "کوردی", "Kurdish (Arabic)", "Indo-European", true],
  ["kv", "kv", "коми кыв", "Komi", "Uralic", false],
  ["kw", "kw", "kernewek", "Cornish", "Indo-European", false],
  ["ky", "ky", "Кыргызча", "Kyrgyz", "Turkic", false],
  ["la", "la", "Latina", "Latin", "Indo-European", false],
  ["lb", "lb", "Lëtzebuergesch", "Luxembourgish", "Indo-European", false],
  ["lg", "lg", "Luganda", "Ganda", "Niger-Congo", false],
  ["li", "li", "Lèmburgs", "Limburgish", "Indo-European", false],
  ["ln", "ln", "lingála", "Lingala", "Niger-Congo", false],
  ["lo", "lo", "ລາວ", "Lao", "Tai-Kadai", false],
  ["lt", "lt", "lietuvių", "Lithuanian", "Indo-European", false],
  ["lu", "lu", "Tshiluba", "Luba-Katanga", "Niger-Congo", false],
  ["lv", "lv", "latviešu", "Latvian", "Indo-European", false],
  ["mg", "mg", "Malagasy", "Malagasy", "Austronesian", false],
  ["mh", "mh", "Kajin M̧ajeļ", "Marshallese", "Austronesian", false],
  ["mi", "mi", "te reo Māori", "Māori", "Austronesian", false],
  ["mk", "mk", "македонски", "Macedonian", "Indo-European", false],
  ["ml", "ml", "മലയാളം", "Malayalam", "Dravidian", false],
  ["mn", "mn", "монгол", "Mongolian", "Mongolic", false],
  ["mn-Cyrl", "mn", "монгол (кирилл)", "Mongolian (Cyrillic)", "Mongolic", false],
  ["mn-Mong", "mn", "ᠮᠣᠩᠭᠣᠯ", "Mongolian (Traditional)", "Mongolic", false],
  ["moh", "moh", "Kanien'kéha", "Mohawk", "Iroquoian", false],
  ["mr", "mr", "मराठी", "Marathi", "Indo-European", false],
  ["ms", "ms", "Bahasa Melayu", "Malay", "Austronesian", false],
  ["ms-Arab", "ms", "بهاس ملايو", "Malay (Jawi)", "Austronesian", true],
  ["mt", "mt", "Malti", "Maltese", "Afro-Asiatic", false],
  ["my", "my", "မြန်မာဘာသာ", "Burmese", "Sino-Tibetan", false],
  ["na", "na", "Dorerin Naoero", "Nauru", "Austronesian", false],
  ["nb", "nb", "norsk bokmål", "Norwegian Bokmål", "Indo-European", false],
  ["nd", "nd", "isiNdebele", "North Ndebele", "Niger-Congo", false],
  ["ne", "ne", "नेपाली", "Nepali", "Indo-European", false],
  ["ng", "ng", "Oshiwambo", "Ndonga", "Niger-Congo", false],
  ["nl", "nl", "Nederlands", "Dutch", "Indo-European", false],
  ["nn", "nn", "norsk nynorsk", "Norwegian Nynorsk", "Indo-European", false],
  ["no", "no", "norsk", "Norwegian", "Indo-European", false],
  ["nr", "nr", "isiNdebele", "South Ndebele", "Niger-Congo", false],
  ["nso", "nso", "Sepedi", "Northern Sotho", "Niger-Congo", false],
  ["nv", "nv", "Diné bizaad", "Navajo", "Na-Dene", false],
  ["ny", "ny", "Chichewa", "Chewa", "Niger-Congo", false],
  ["oc", "oc", "occitan", "Occitan", "Indo-European", false],
  ["oj", "oj", "ᐊᓂᔑᓈᐯᒧᐎᓐ", "Ojibwe", "Algic", false],
  ["om", "om", "Afaan Oromoo", "Oromo", "Afro-Asiatic", false],
  ["or", "or", "ଓଡ଼ିଆ", "Odia", "Indo-European", false],
  ["os", "os", "ирон æвзаг", "Ossetian", "Indo-European", false],
  ["pa", "pa", "ਪੰਜਾਬੀ", "Punjabi", "Indo-European", false],
  ["pa-Arab", "pa", "پنجابی", "Punjabi (Shahmukhi)", "Indo-European", true],
  ["pi", "pi", "पालि", "Pali", "Indo-European", false],
  ["pl", "pl", "polski", "Polish", "Indo-European", false],
  ["ps", "ps", "پښتو", "Pashto", "Indo-European", true],
  ["pt", "pt", "português", "Portuguese", "Indo-European", false],
  ["pt-BR", "pt", "português (Brasil)", "Portuguese (Brazil)", "Indo-European", false],
  ["pt-PT", "pt", "português (Portugal)", "Portuguese (Portugal)", "Indo-European", false],
  ["qu", "qu", "Runa Simi", "Quechua", "Quechuan", false],
  ["rm", "rm", "rumantsch", "Romansh", "Indo-European", false],
  ["rn", "rn", "Ikirundi", "Rundi", "Niger-Congo", false],
  ["ro", "ro", "română", "Romanian", "Indo-European", false],
  ["ru", "ru", "русский", "Russian", "Indo-European", false],
  ["rw", "rw", "Kinyarwanda", "Kinyarwanda", "Niger-Congo", false],
  ["sa", "sa", "संस्कृतम्", "Sanskrit", "Indo-European", false],
  ["sc", "sc", "sardu", "Sardinian", "Indo-European", false],
  ["sd", "sd", "سنڌي", "Sindhi", "Indo-European", true],
  ["se", "se", "davvisámegiella", "Northern Sami", "Uralic", false],
  ["sg", "sg", "yângâ tî sängö", "Sango", "Creole", false],
  ["si", "si", "සිංහල", "Sinhala", "Indo-European", false],
  ["sk", "sk", "slovenčina", "Slovak", "Indo-European", false],
  ["sl", "sl", "slovenščina", "Slovenian", "Indo-European", false],
  ["sm", "sm", "gagana Samoa", "Samoan", "Austronesian", false],
  ["sn", "sn", "chiShona", "Shona", "Niger-Congo", false],
  ["so", "so", "Soomaali", "Somali", "Afro-Asiatic", false],
  ["sq", "sq", "shqip", "Albanian", "Indo-European", false],
  ["sr", "sr", "српски", "Serbian", "Indo-European", false],
  ["sr-Cyrl", "sr", "српски (ћирилица)", "Serbian (Cyrillic)", "Indo-European", false],
  ["sr-Latn", "sr", "srpski (latinica)", "Serbian (Latin)", "Indo-European", false],
  ["ss", "ss", "SiSwati", "Swati", "Niger-Congo", false],
  ["st", "st", "Sesotho", "Southern Sotho", "Niger-Congo", false],
  ["su", "su", "Basa Sunda", "Sundanese", "Austronesian", false],
  ["sv", "sv", "svenska", "Swedish", "Indo-European", false],
  ["sw", "sw", "Kiswahili", "Swahili", "Niger-Congo", false],
  ["syc", "syc", "ܣܘܪܝܝܐ", "Classical Syriac", "Afro-Asiatic", true],
  ["ta", "ta", "தமிழ்", "Tamil", "Dravidian", false],
  ["te", "te", "తెలుగు", "Telugu", "Dravidian", false],
  ["tg", "tg", "тоҷикӣ", "Tajik", "Indo-European", false],
  ["th", "th", "ไทย", "Thai", "Tai-Kadai", false],
  ["ti", "ti", "ትግርኛ", "Tigrinya", "Afro-Asiatic", false],
  ["ti-Ethi", "ti", "ትግርኛ (ኢትዮጵያ)", "Tigrinya (Ethiopic)", "Afro-Asiatic", false],
  ["tiv", "tiv", "Tiv", "Tiv", "Niger-Congo", false],
  ["tk", "tk", "Türkmençe", "Turkmen", "Turkic", false],
  ["tl", "tl", "Tagalog", "Tagalog", "Austronesian", false],
  ["tn", "tn", "Setswana", "Tswana", "Niger-Congo", false],
  ["to", "to", "lea faka-Tonga", "Tonga", "Austronesian", false],
  ["tr", "tr", "Türkçe", "Turkish", "Turkic", false],
  ["ts", "ts", "Xitsonga", "Tsonga", "Niger-Congo", false],
  ["tt", "tt", "татарча", "Tatar", "Turkic", false],
  ["tw", "tw", "Twi", "Twi", "Niger-Congo", false],
  ["ty", "ty", "reo Tahiti", "Tahitian", "Austronesian", false],
  ["ug", "ug", "ئۇيغۇرچە", "Uyghur", "Turkic", true],
  ["uk", "uk", "українська", "Ukrainian", "Indo-European", false],
  ["ur", "ur", "اردو", "Urdu", "Indo-European", true],
  ["uz", "uz", "O'zbek", "Uzbek", "Turkic", false],
  ["uz-Latn", "uz", "O'zbek (lotin)", "Uzbek (Latin)", "Turkic", false],
  ["uz-Cyrl", "uz", "Ўзбек (кирилл)", "Uzbek (Cyrillic)", "Turkic", false],
  ["uz-Arab", "uz", "اوزبیک", "Uzbek (Arabic)", "Turkic", true],
  ["ve", "ve", "Tshivenḓa", "Venda", "Niger-Congo", false],
  ["vi", "vi", "Tiếng Việt", "Vietnamese", "Austroasiatic", false],
  ["vo", "vo", "Volapük", "Volapük", "Constructed", false],
  ["wa", "wa", "walon", "Walloon", "Indo-European", false],
  ["wo", "wo", "Wolof", "Wolof", "Niger-Congo", false],
  ["xh", "xh", "isiXhosa", "Xhosa", "Niger-Congo", false],
  ["yi", "yi", "ייִדיש", "Yiddish", "Indo-European", true],
  ["yo", "yo", "Yorùbá", "Yoruba", "Niger-Congo", false],
  ["za", "za", "Sawndip", "Zhuang", "Tai-Kadai", false],
  ["zh", "zh", "中文", "Chinese", "Sino-Tibetan", false],
  ["zh-Hans", "zh", "简体中文", "Chinese (Simplified)", "Sino-Tibetan", false],
  ["zh-Hant", "zh", "繁體中文", "Chinese (Traditional)", "Sino-Tibetan", false],
  ["zu", "zu", "isiZulu", "Zulu", "Niger-Congo", false],
];

const TRANSLATED = new Set(["en", "en-GB", "en-NG"]);
const PARTIAL = new Set([
  "fr",
  "ar",
  "es",
  "ha",
  "hi",
  "ig",
  "ja",
  "pt",
  "sw",
  "yo",
  "zh",
]);

function statusOf(tag: string): TranslationStatus {
  if (TRANSLATED.has(tag)) return "translated";
  if (PARTIAL.has(tag)) return "partial";
  return "unavailable";
}

export const LANGUAGES: LanguageEntry[] = RAW.map(
  ([tag, iso, native, english, family, rtl]) => ({
    tag,
    iso,
    native,
    english,
    family,
    rtl,
    status: statusOf(tag),
  })
);

export const LANGUAGE_MAP: ReadonlyMap<string, LanguageEntry> = new Map(
  LANGUAGES.map((entry) => [entry.tag, entry])
);

export function getLanguage(tag: string): LanguageEntry | undefined {
  return LANGUAGE_MAP.get(tag);
}

export function isRtl(tag: string): boolean {
  return LANGUAGE_MAP.get(tag)?.rtl ?? false;
}

/* Strict BCP 47 well-formedness (Intl.Locale parse). Registration in
 * this catalogue is a separate check (getLanguage). */
export function isValidTag(tag: string): boolean {
  if (typeof tag !== "string" || tag.length === 0 || tag.length > 35) {
    return false;
  }
  try {
    new Intl.Locale(tag);
    return true;
  } catch {
    return false;
  }
}

/* Base-language RTL set for the no-flash inline script in
 * app/layout.tsx (interpolated at module load: single source). */
export const RTL_BASE_LANGS: readonly string[] = [
  ...new Set(
    LANGUAGES.filter((entry) => entry.rtl).map(
      (entry) => entry.tag.split("-")[0] as string
    )
  ),
].sort();

/* BCP 47 lookup fallback: "fr-CA" -> "fr" -> "en". Returns the first tag
 * with a dictionary, defaulting to the configured fallback language. */
export function resolveDictionaryTag(
  tag: string,
  available: ReadonlySet<string>,
  fallback = "en"
): string {
  const subtags = tag.split("-");
  while (subtags.length > 0) {
    const candidate = subtags.join("-");
    if (available.has(candidate)) return candidate;
    subtags.pop();
  }
  return fallback;
}

/* Best-match a browser language list against the registry: exact tag,
 * then base language, then the fallback. Pure: deterministic in tests. */
export function matchBrowserLocales(
  requested: readonly string[],
  fallback = "en"
): string {
  for (const raw of requested) {
    const tag = raw.trim();
    if (tag === "") continue;
    if (LANGUAGE_MAP.has(tag)) return tag;
    const base = tag.split("-")[0] ?? "";
    if (base !== "" && LANGUAGE_MAP.has(base)) return base;
  }
  return fallback;
}
