import Foundation
import ImageIO
for path in CommandLine.arguments.dropFirst() {
    let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil)!
    let p = CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as! [String: Any]
    let g = p[kCGImagePropertyGPSDictionary as String] as? [String: Any] ?? [:]
    let e = p[kCGImagePropertyExifDictionary as String] as? [String: Any] ?? [:]
    print(path.split(separator: "/").last!, g["Latitude"] ?? "-", g["LatitudeRef"] ?? "-", g["Longitude"] ?? "-", g["LongitudeRef"] ?? "-", g["Altitude"] ?? "-", g["DateStamp"] ?? "-", g["TimeStamp"] ?? "-", e["DateTimeOriginal"] ?? "-")
}
