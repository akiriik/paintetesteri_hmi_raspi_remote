# Painetesterin toimintaloki

Paikallinen loki: ~/.local/share/painetesteri_hmi/runtime_logs/YYYYMMDD-HH.jsonl

Loki on git-työpuun ulkopuolella, joten se ei estä Raspin päivitysnappia.
Loki sisältää vain tapahtuma-ajat (UTC), aseman, ohjelmanumeron,
tilakoodit, käskyt ja estojen syyt. Sarjanumeroita, mittaustuloksia,
käyttäjätietoja tai vapaamuotoista virhetekstiä ei lähetetä.

## GitHub: sama repo, erillinen diagnostics-haara

**TÄRKEÄÄ:** Repo akiriik/paintetesteri_hmi_raspi_remote on JULKINEN.
Myös diagnostics-haaran lokit ovat julkisesti nähtävissä.
Älä lisää niihin luottamuksellista sisältöä.

Automaattinen GitHub-siirto aktivoituu vasta, kun Raspberrylle on
asennettu rajattu GitHub-tunniste. Paikallinen loki toimii aina ilman
tunnistetta ja ilman internetyhteyttä.

1. Luo GitHubissa Fine-grained Personal Access Token:
   resource owner akiriik, vain repo paintetesteri_hmi_raspi_remote,
   Contents = Read and write. Muita oikeuksia ei tarvita.
2. SSH-yhteys Raspberryn omana käyttäjänä. Suorita:

       install -d -m 700 ~/.config/painetesteri_hmi
       umask 077
       read -rs -p "GitHub token: " TOKEN; echo
       printf '%s' "$TOKEN" > ~/.config/painetesteri_hmi/github_token
       unset TOKEN
       chmod 600 ~/.config/painetesteri_hmi/github_token

3. Sovellus tunnistaa tunnistetiedoston seuraavalla lähetysyrityksellä.
   Tokenia ei saa tallentaa repoon eikä lähettää keskusteluun.

Loki päivittyy seuraavaan polkuun onnistuneen lähetyksen jälkeen:

https://github.com/akiriik/paintetesteri_hmi_raspi_remote/tree/diagnostics/runtime-logs

Palveluun tallentuu tunnin JSONL-tiedostoja polulla
runtime-logs/unit-<anonymisoitu laitetunnus>/YYYYMMDD/HH.jsonl.
Päivitys tapahtuu 5 minuutin välein tai vikatapahtumasta, kuitenkin
enintään yksi lähetysyritys minuutissa. Lähetys on taustasäikeessä.

## Vianetsinnän keskeiset tapahtumat

- jig_manual_blocked, reason = miksi käsikäyttö ei ole sallittu
- jig_manual_denied = hylätty painallus
- jig_command_queued / jig_start_ack / jig_state_changed
- jig_manual_timeout / jig_stop_error / jig_stop_ack
- fortest_status_changed (esim. 3 -> 0)
- valve_write_queued / valve_write_ack / valve_ack_timeout
- pressure_release_timer_started / pressure_release_timer_elapsed
- test_result_accepted, start_requested, stop_requested

Pääsäikeen jumitallenne säilyy paikallisesti:

~/.local/share/painetesteri_hmi/ui_freeze_diagnostics.log

Sitä EI siirretä automaattisesti julkiseen GitHub-repoon.

## Toimintarajat

Lokin vika ei keskeytä laiteohjausta. Jigivaraus vapautetaan vain
valmistuneen sekvenssin tai kuitatun STOPin jälkeen. Jos Optan
tilaa ei voida vahvistaa, jigiohjaus pysyy lukittuna.
Fyysistä turvapiiriä ei saa korvata ohjelmallisella STOPilla.

Git-päivitys tai -palautus ei muuta Optan firmwarea eikä poista
paikallisia lokitiedostoja.
