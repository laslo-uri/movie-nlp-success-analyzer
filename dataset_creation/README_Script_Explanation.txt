1.fetch_tmdb.py

    Kreiranje osnove baze sakupljajući filmove iz prošlih 70 godina.

    Koristeći API pozive, sistematski češlja TMDB kako bi izvuklo 500 top filmova po godini.

    Na godišnjoj bazi čuva CSV checkpoints kako bi podaci bili bezbedni u slučaju da skripta pukne na pola posla.

2. enrich_tmdb_data.py

    Služi za snimanje konkretnih finansijskih metrika (budget i revenue) koje nam trebaju za računanje ROI (naš target za Market Success).

    Uzima osnovnu listu i gađa TMDB API za te detalje i jako bitne IMDb ID-jeve.

    Pametno radi batch processing i ima crash recovery, pa automatski pauzira kad udarimo u API rate limite kako nas ne bi blokirali.

3. fetch_awards.py

    Cilj je da napravimo "ground truth" listu za naš Critical Success model.

    Preko zvaničnog Wikipedia API-ja skida podatke za glavne filmske nagrade (Oskari, BAFTA, Zlatni globus, itd.).

    Glavna snaga joj je što parsira potpuno haotične HTML tabele, čisti naslove i pakuje sve to u jedan čist CSV spisak nagrađivanih filmova.

4. merge_and_filter.py

    Radi kao naš "Great Filter" da očisti dataset od irelevantnih filmova i đubreta.

    Spaja TMDB metapodatke, finansije i Wikipedia nagrade u jednu masivnu master tabelu.

    Strogo propušta samo filmove koji prolaze barem jedan od tri uslova: imaju validne finansijske podatke, osvojili su neku veliku nagradu ili imaju gomilu glasova (dokaz da je pravi film, a ne neki studentski projekat).

5. scrape_transcripts.py

    Glavni alat za nabavljanje samog teksta (dijaloga) koji će naš NLP model zapravo da žvaće.

    Glumi pravi web browser (menja nasumične User-Agente) da bi zaobišao bot zaštite i skrejpovao titlove direktno sa neta.

    Koristi fuzzy string matching logiku da bi bio apsolutno siguran da naslov filma koji skidamo zapravo odgovara onom iz naše baze.

6. audit_files.py

    Pre nego što ubacimo tekst u ML model, ova skripta radi provere da li je neki fajl korumpiran tokom skidanja.

    Skenira ceo folder sa skinutim fajlovima i traži skrivene greške.

    Flaguje fajlove koji su sumnjivo mali (ispod 2KB) ili u sebi greškom sadrže HTML error poruke tipa "404 Not Found" ili "Cloudflare block".

7. clean_bad_files.py

    Fizički briše loše fajlove koje je audit skripta našla, da nam ne bi upropastili NLP procesiranje vokabulara.

    Čita audit report i direktno briše te fajlove sa hard diska.

    Ima ugrađen safety check, pa traži da ručno u terminalu ukucamo potvrdu ("DELETE") pre nego što bilo šta trajno obriše, čisto da ne obrišemo sve slučajno.

8. create_downloaded_manifest.py

    Nakon čišćenja, proverava šta nam je zapravo ostalo od validnih i upotrebljivih podataka.

    Upoređuje tekstualne fajlove koji fizički postoje na disku sa našom filtriranom master bazom.

    Pravi finalni "Source of Truth" CSV manifest, što garantuje da svaki red u datasetu za treniranje ima svoj pripadajući validan .txt fajl.

9. check_balance.py

    Proverava da li je naš finalni dataset statistički okej i spreman za Machine Learning fazu.

    Analizira class imbalance za naše target varijable (npr. gleda koliko zapravo imamo dobitnika nagrada naspram onih koji nisu dobili).

    Služi kao rana dijagnostika koja nam javlja ako ćemo morati da koristimo SMOTE balansiranje klasa pre samog treniranja modela.

10. compare_datasets.py

    Vizuelno proverava da li smo ovim web scrapingom slučajno uneli neki bias u podatke.

    Upoređuje listu filmova koje smo prvobitno targetirali sa onima koje smo na kraju uspešno skinuli.

    Automatski generiše i čuva pie i bar chart grafike (spremne za projektnu dokumentaciju) koji nam pokazuju da li se skrejper možda više mučio sa starijim filmovima ili specifičnim žanrovima.