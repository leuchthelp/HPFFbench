Projektaufgabe: Evaluierung von Dateiformaten (HDF5, NetCDF, Zarr) auf verschiedenen Systemen
Zielsetzung:

Das Projekt zielt darauf ab, die Leistung verschiedener wissenschaftlicher Dateiformate – insbesondere HDF5, NetCDF und Zarr – auf unterschiedlichen Speichersystemen zu evaluieren. Ein besonderes Augenmerk liegt dabei auf dem Leistungsvergleich unter Nutzung spezifischer Features wie Subfiling und asynchronem I/O sowie der Kompatibilität zwischen NetCDF und Zarr. Hierbei soll auch die Entwicklung von Zarr 3 betrachtet und die Implementierung in NetCDF geprüft werden. Die Tests werden auf unterschiedlichen Speichersystemen wie Lustre (HDD/Flash), Ceph und weiteren durchgeführt.
Aufgaben:

Leistungsvergleich verschiedener Dateiformate:

    Evaluierung der Formate HDF5, NetCDF und Zarr (inkl. Zarr 3). 
- [x]    Untersuchung der Parallelität und der Lese- und Schreibgeschwindigkeit auf unterschiedlichen Dateisystemen (z. B. Lustre auf HDD und Flash, Ceph).

Features-Analyse:

    Vergleich der Leistung und Effizienz bei Nutzung von Subfiling, asynchronem I/O und parallelem Zugriff.
    Testen der Formate mit verschiedenen Zugriffsmustern (sequentiell, zufällig, parallel) auf Datensätze in unterschiedlich vielen Dateien und verschiedener Größe.

Implementierung und Kompatibilität von Zarr 3 in NetCDF:

    Untersuchung der Kompatibilität zwischen NetCDF und Zarr. -Implementierung und Validierung der Integration von Zarr 3 in NetCDF.

Erweiterung des Benchmarks:

    Anpassung und Erweiterung des bestehenden Benchmarks numio zur Berücksichtigung der neuen Anforderungen, inklusive:
    Subfiling-Mechanismen.
    Asynchronem I/O unter Berücksichtigung zusätzlicher Berechnungen.
    Paralleles Lesen und Schreiben von Daten.

Testdaten und Kompression:

    Generierung sinnvoller Testdaten, die verschiedene Kompressionsfaktoren berücksichtigen.
    Evaluation der Kompressionseffizienz und -auswirkungen auf die Zugriffszeiten.
    Für ansnchrone Kompression müssen ebenfall realistische zusätzliche Berechnungen berücksichtigt werden

Zusammenfassung und Dokumentation:

    Auswertung der Testergebnisse in Hinblick auf Leistungsmerkmale wie Durchsatz, Latenz und Skalierbarkeit.
    Dokumentation der gewonnenen Erkenntnisse sowie der Implementierungsschritte für die Integration von Zarr 3 in NetCDF.

Anforderungen:

Praktische Erfahrungen mit parallelen Dateisystemen (z. B. Lustre, Ceph).
Kenntnisse der wissenschaftlichen Dateiformate HDF5, NetCDF und Zarr.
Vertrautheit mit Benchmarking-Tools für Speicher- und I/O-Leistung.
Ergebnis:

Am Ende des Projekts liegt eine umfassende Analyse der Leistungsfähigkeit und Kompatibilität der genannten Dateiformate auf verschiedenen Systemen vor. Zudem ist der Benchmark entsprechend erweitert und es wurden konkrete Implementierungsschritte für die Integration von Zarr 3 in NetCDF dokumentiert.


Next two weeks: 


Threading, C Wrapper for python to use NCZarr v2 and v3. For this build both current and .rc2 library of NetCDF4 