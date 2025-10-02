# Future Improvements Checklist

## Pump Curves
- Replace demo pump curves with real Pentair, Hayward, Jandy CSVs
- Add support for variable speed curves (multi-RPM)

## Hydraulics
- Improve equivalent length per fitting by pipe size
- Add brand-specific equipment head losses (filters, heaters, salt cells)

## Heater Sizing
- Account for environmental heat loss factors

## Electrical
- Replace placeholder AWG table with NEC-compliant data
- Add breaker sizing + material type (copper/aluminum)

## Labor Model
- Expand flat rates into per-equipment multipliers
- Add auto-estimate for pad rebuilds

## Catalog / BOM
- Create catalog CSV of parts (pump models, filters, heaters, cells)
- Map calculated specs → part numbers
- Generate BOM with pricing + markup

## Output
- Add client-facing PDF proposal generator
- Keep internal-only design sheet
