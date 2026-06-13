# -*- coding: utf-8 -*-
"""Embedded language training data (composed prose, no external files) for
character n-gram LMs: English, German, Polish, Portuguese.
CONTROL_* texts are disjoint from TRAIN_* texts (different topics/wording),
used only as plaintext for the synthetic homophonic control ciphers."""

TRAIN_EN = """
The old harbour town woke slowly under a grey morning sky. Fishermen dragged
their boats across the wet sand while gulls circled overhead and cried into
the wind. In the narrow streets behind the quay, shopkeepers opened their
shutters one by one, and the smell of fresh bread drifted from the bakery on
the corner. Nobody hurried. The town had kept the same rhythm for three
hundred years, and it saw no reason to change now.
Maren walked along the sea wall with her hands deep in her coat pockets. She
had come back after ten years in the capital, and everything seemed smaller
than she remembered. The lighthouse at the end of the pier still flashed its
slow white signal, though the keeper had long since been replaced by a small
automatic lamp. Her father used to climb those stairs every evening. She
could still hear his heavy boots on the iron steps if she closed her eyes.
The letter that had brought her home lay folded in her pocket. It was short,
written in her brother's careless hand, and it said only that the house would
be sold unless she came to settle the matter in person. She had read it forty
times on the train and still did not know what she felt. The house was old
and the roof leaked and the garden had gone wild years ago, but it was the
last thing that held the family to this place.
At the end of the wall she turned and looked back at the town. Smoke rose
from a dozen chimneys and hung low over the red roofs. A dog barked somewhere
near the market square. It would be easy, she thought, to stay a week, sign
the papers, and go back to her quiet flat and her quiet job. It would be
easy, and it would be wrong, though she could not yet say why.
Her brother met her at the gate with a smile that did not reach his eyes. He
had grown heavier and older, and there were lines around his mouth that she
did not remember. They drank coffee in the cold kitchen and spoke carefully
about the weather, about the neighbours, about everything except the house.
Outside the window the apple tree their mother had planted scratched its bare
branches against the glass.
When he finally spread the documents on the table, she saw that he had
already signed his half. The buyer was a hotel company from the city that
wanted to pull the house down and build apartments for summer guests. Good
money, he said, more than the place was worth. She looked at the pen he
offered her and put her hands back in her pockets. Not yet, she said. Give
me a few days. He shrugged, but she saw the worry move across his face like
a cloud across water.
That night she slept in her childhood room under the sloping roof. The rain
came in after midnight, soft at first, then steady, and she lay awake
listening to the drops strike the window. Somewhere below, the stairs creaked
the way they always had, on the seventh step, where the wood had warped the
year of the great storm. She knew every sound of this house the way she knew
her own breathing. In the morning she would walk through every room and open
every cupboard, and then she would decide.
The decision, when it came, surprised her with its simplicity. She stood in
the attic among boxes of old photographs and her father's charts of the
coastal waters, and she understood that she was not the kind of person who
could trade memory for money. She would buy out her brother's half, rent out
the rooms in summer, and keep the lighthouse view for the winters. The bank
would complain and the roof would still leak, but the apple tree would stay,
and the seventh stair would go on creaking for whoever came after her.
Work began in the spring. Carpenters replaced the rotten beams, and a young
painter from the village did the windows in exchange for a month of dinners.
Maren learned to mix mortar and to argue about prices for timber. Her hands
grew rough and her sleep grew deep. Sometimes, standing on a ladder with
paint in her hair, she caught herself singing songs she had not thought of
since she was a child. The town watched, nodded, and said nothing, which was
its way of approving.
The first guests arrived in June, a teacher and her two sons who wanted
nothing more than a beach and a kitchen and a view of the water. The boys
found the old charts in the attic and spent a week mapping imaginary voyages
to islands that did not exist. Their mother sat in the garden under the apple
tree reading until the light failed. When they left she wrote in the guest
book that the house felt like a place where time had agreed to slow down, and
that they would return every summer as long as she could manage it.
In the autumn her brother came to visit. He walked through the bright rooms
without speaking, touched the new banister, and stood a long time at the
window where the lamp of the lighthouse swept its patient arc over the dark
sea. You were right, he said at last, and that was all he ever said about it.
They ate dinner in the warm kitchen, and afterwards he fixed the latch on the
garden gate without being asked, the way their father would have done it.
Winter came early that year and stayed late. The harbour froze along its
edges for the first time in a decade, and the fishermen hauled their boats
high onto the shingle and mended nets in the smoky warmth of the boathouse.
Maren kept the front room open as a kind of library, and on the worst
evenings half the street seemed to gather there, playing cards under the old
charts and arguing happily about nothing. She wrote letters to the teacher
in the city, long ones, full of small news, and the replies came back full
of questions about the sea. When the ice broke up in March the whole town
walked out to watch it go, groaning and cracking down the channel toward the
open water, and the children threw stones onto the moving floes and made
wishes, because that was what had always been done and nobody remembered why.
The second summer was easier than the first. She knew now which rooms caught
the morning sun and which guests wanted talk and which wanted silence. The
roof was sound at last, the bank had stopped writing, and the painter from
the village had become a friend who came on Sundays whether there was work or
not. Sometimes in the long evenings she climbed the lighthouse stairs, her
boots loud on the iron the way her father's had been, and stood at the top
while the lamp turned, watching the fishing boats draw their slow white lines
home across the bay, and she could not remember anymore what it was that the
city had seemed to offer, all those years, that this had ever lacked.
"""

TRAIN_DE = """
Der alte Bahnhof lag am Rand der Stadt, dort wo die Felder begannen und die
Strassen keine Namen mehr hatten. Seit zwanzig Jahren hielt hier kein Zug
mehr, aber jeden Morgen ging der alte Brenner mit seinem Hund die Gleise
entlang, als warte er noch immer auf einen Besucher, der nie ankam. Die
Leute im Dorf hielten ihn fuer wunderlich, doch sie gruessten ihn freundlich,
denn er hatte ihnen allen einmal geholfen, als die Zeiten schlechter waren.
Im Sommer kam eine junge Frau aus der Stadt und mietete das kleine Haus neben
der Kirche. Sie sagte, sie wolle ein Buch schreiben, und brauchte dafuer
Ruhe. Die Nachbarn brachten ihr Eier und Brot und stellten keine Fragen, was
sie als grosse Freundlichkeit verstand. Jeden Nachmittag sass sie unter dem
Nussbaum im Garten und schrieb mit der Hand in dicke Hefte, und wenn der Wind
durch die Blaetter ging, hielt sie inne und hoerte zu, als spreche jemand mit
ihr.
Eines Tages begegnete sie dem alten Brenner an den Gleisen. Er erzaehlte ihr
vom letzten Zug, der hier gehalten hatte, und von den Menschen, die damals
ausgestiegen waren. Seine Schwester sei darunter gewesen, sagte er, mit zwei
Koffern und einem Kind auf dem Arm, und sie habe versprochen wiederzukommen,
sobald drueben alles geregelt sei. Dann sei der Winter gekommen und der
naechste, und die Strecke sei stillgelegt worden, und das Versprechen sei
geblieben wie ein Stein im Feld, den niemand mehr bewegen konnte.
Die Frau schrieb diese Geschichte auf, erst nur fuer sich, dann fuer ihr
Buch. Sie aenderte die Namen und das Dorf, aber die Gleise liess sie, wie sie
waren, rostig und gerade und voller Geduld. Als das Buch im naechsten Jahr
erschien, schickte sie dem alten Mann ein Exemplar mit einer Widmung. Er
stellte es ungelesen auf das Regal neben die Uhr, doch jedem Besucher zeigte
er es und sagte, hier stehe seine Schwester drin, und der Zug komme noch.
Im Herbst beschloss die Gemeinde, den Bahnhof abzureissen und auf dem
Gelaende einen Parkplatz zu bauen. Es gab eine Versammlung im Gasthaus, bei
der viel geredet und wenig gesagt wurde. Der Buergermeister sprach von
Fortschritt und von Kosten, und die meisten nickten, weil Nicken einfacher
ist als Widerspruch. Da stand die Frau aus der Stadt auf und las die Stelle
aus ihrem Buch vor, in der die Schwester aus dem Zug steigt und das Kind auf
den Bahnsteig setzt und sagt, wartet auf uns, wir kommen wieder.
Es wurde sehr still im Saal. Der Wirt vergass das Zapfen, und die Uhr an der
Wand schlug neun, ohne dass jemand sie beachtete. Schliesslich erhob sich
der Schmied, ein schwerer Mann, der sonst nie etwas sagte, und meinte, man
koenne den Parkplatz auch hinter dem Friedhof bauen, da sei genug Platz und
niemand muesse etwas abreissen. So wurde es beschlossen, nicht aus Vernunft,
sondern aus etwas Aelterem, fuer das die Versammlung keinen Namen hatte.
Der Bahnhof blieb stehen. Die Jugend des Dorfes strich ihn im Fruehjahr neu,
die Tischlerei stiftete Baenke fuer den Bahnsteig, und der Lehrer haengte
alte Fotografien in den Wartesaal. Im Sommer kamen Wanderer vorbei und
tranken Kaffee, den die Baeuerin vom Hof nebenan ausschenkte, und manche
fragten, wann denn der naechste Zug fahre. Dann laechelten die Leute vom Dorf
und sagten, das wisse man nicht so genau, aber warten koenne man hier besser
als irgendwo sonst.
Der alte Brenner starb im Februar, friedlich und im Schlaf, wie es im Dorf
hiess. Sein Hund lief noch ein Jahr lang jeden Morgen die Gleise entlang,
ehe er sich der Baeuerin anschloss und ein Hofhund wurde. Auf dem Grabstein
des Alten steht kein Spruch, nur sein Name und darunter, klein und sauber
gemeisselt, eine Lokomotive mit drei Wagen. Die Kinder des Dorfes glauben,
wer den Stein beruehrt und sich etwas wuenscht, dessen Wunsch faehrt mit dem
naechsten Zug davon und kommt eines Tages erfuellt zurueck.
Die Frau aus der Stadt blieb laenger, als sie geplant hatte. Aus dem einen
Sommer wurden drei, dann kaufte sie das kleine Haus neben der Kirche und
liess sich Buecherregale in alle Zimmer bauen. Sie schreibt jetzt an einer
Geschichte des Dorfes, fuer die ihr die Alten erzaehlen, was sie noch wissen,
und die Jungen bringen ihr bei, wie man mit dem Traktor faehrt. Abends sitzt
sie oft auf der Bank am Bahnsteig und sieht zu, wie das Licht hinter den
Feldern versinkt, und manchmal, wenn der Wind richtig steht, meint sie in der
Ferne ein Pfeifen zu hoeren, das naeher kommt.
Im folgenden Jahr richtete das Dorf im Wartesaal eine kleine Schule fuer die
Ferienkinder ein, die im Sommer zu den Grosseltern kamen und sich langweilten.
Die Frau aus der Stadt las mit ihnen Geschichten, der Schmied zeigte ihnen,
wie man Hufeisen biegt, und die Baeuerin lehrte sie, Brot zu backen, das
nach etwas schmeckte. Am Ende des Sommers fuehrten die Kinder auf dem
Bahnsteig ein Theaterstueck auf, das von einem Zug handelte, der nur
anhaelt, wo jemand wartet, der wirklich etwas hofft. Das halbe Dorf sass
auf den neuen Baenken und klatschte, und einige der Alten wischten sich die
Augen und behaupteten hinterher, es sei der Wind gewesen. So vergingen die
Jahre, ohne dass viel geschah und ohne dass etwas fehlte. Die Stadt rueckte
naeher, die Strassen wurden breiter, und manch einer aus dem Dorf fuhr nun
taeglich zur Arbeit hinueber. Aber der alte Bahnhof blieb, frisch
gestrichen und mit Blumen vor dem Wartesaal, und wer abends mit Sorgen
hinausging und sich auf die Bank setzte, der fand dort meistens schon
jemanden sitzen, der zuhoeren konnte, und kam leichter nach Hause zurueck,
als er gegangen war. Und wenn die Kinder fragten, warum man einen Bahnhof
behalte, an dem kein Zug mehr halte, dann sagten die Eltern, ein Dorf
brauche einen Ort, an dem das Warten schoen ist, denn das meiste im Leben
sei Warten, und man koenne es gut lernen oder schlecht.
"""

TRAIN_PL = """
Stary mlyn nad rzeka stal pusty od wielu lat. Dzieci ze wsi balysie tam
chodzic, bo starsi opowiadali, ze noca slychac w nim kroki i skrzypienie
kola, ktore przeciez dawno przestalo sie obracac. Tylko Marta, corka
mlynarza, ktory wyjechal do miasta, przychodzila czasem nad wode i siadala
na progu, patrzac jak rzeka plynie miedzy kamieniami.
Pewnego lata do wsi przyjechal mlody nauczyciel. Szukal spokojnego miejsca,
zeby pisac i uczyc dzieci w malej szkole przy kosciele. Zamieszkal u
gospodarza na koncu drogi i szybko poznal wszystkich we wsi. Ludzie mowili
mu o mlynie, o tym, ze ziemia tam niedobra i ze lepiej budowac gdzie indziej,
ale on sluchal i usmiechal sie tylko, bo widzial w starym budynku cos, czego
inni nie widzieli.
Jesienia nauczyciel zaczal naprawiac dach mlyna. Pomagali mu najpierw
chlopcy ze szkoly, potem ich ojcowie, a w koncu nawet stary kowal, ktory
pamietal jeszcze czasy, kiedy kolo sie krecilo i cala wies przywozila tu
zboze. Praca szla powoli, ale nikt sie nie spieszyl. Wieczorami siadali na
brzegu i mowili o tym, co bedzie, kiedy mlyn znowu ozyje, i kazdy widzial to
inaczej, i wlasnie to bylo najpiekniejsze.
Zima przyszla wczesnie i przykryla wies sniegiem. W mlynie palilo sie
swiatlo, bo nauczyciel urzadzil tam izbe z ksiazkami, gdzie dzieci mogly
przychodzic po lekcjach. Marta przynosila im chleb i mleko, a czasem
zostawala dluzej i sluchala, jak czytaja na glos. Kiedy wiatr uderzal w
okna, najmlodsi mowili, ze to duch mlynarza, ale teraz nikt sie juz nie bal,
bo dom byl cieply i pelen glosow.
Na wiosne rzeka wezbrala i woda podeszla pod sam prog. Cala wies przyszla
ratowac ksiazki, ludzie podawali je sobie z rak do rak az na gore, i nawet
ci, ktorzy nigdy nic nie czytali, niesli je ostroznie jak chleb. Woda opadla
po trzech dniach i okazalo sie, ze stare kolo, poruszone przez prad, znowu
sie obraca. Stali wszyscy na brzegu i patrzyli, jak woda spada z lopat, i
nikt nic nie mowil, bo sa takie chwile, kiedy slowa tylko przeszkadzaja.
Latem odbylo sie w mlynie pierwsze wesele, corki kowala z chlopakiem z
sasiedniej wsi. Tanczono na nowym mostku i na trawie, a stoly staly tam,
gdzie kiedys sypano zboze. Nauczyciel siedzial z boku i patrzyl na to
wszystko, i myslal, ze ksiazka, ktora chcial napisac, dzieje sie sama, tylko
nie na papierze. Marta przyniosla mu kawalek tortu i usiadla obok, i tak juz
zostalo, jak to we wsi, gdzie wszystko widac i nic nie trzeba ogłaszac.
Po latach, kiedy pytano go, czemu zostal, wzruszal ramionami i mowil, ze
czlowiek nie wybiera miejsca, tylko miejsce wybiera czlowieka. Mlyn stoi do
dzisiaj, kolo obraca sie wolno, a w izbie na gorze dzieci czytaja te same
ksiazki, ktore kiedys ratowano przed woda, i niektore maja jeszcze na
okladkach slady tamtej wiosny.
"""

TRAIN_PT = """
A pequena livraria ficava numa rua estreita perto do rio, entre uma
alfaiataria e uma casa de cha. O velho Joaquim abria as portas todas as
manhas as nove em ponto, limpava o po das estantes e sentava se atras do
balcao a ler, esperando os poucos clientes que ainda subiam aquela rua. A
cidade tinha mudado, os predios novos cresciam do outro lado do rio, mas ali
o tempo parecia ter feito um acordo com as pedras da calcada.
Numa tarde de outubro entrou uma rapariga com uma mochila gasta e perguntou
se ele comprava livros usados. Trazia uma caixa que fora do avo, disse, e
precisava do dinheiro para terminar os estudos. Joaquim abriu a caixa
devagar e encontrou, entre romances comuns, uma primeira edicao que
procurava havia trinta anos. Podia te la comprado por pouco, a rapariga nao
sabia o que tinha, mas ele pousou os oculos, olhou a para ela e disse lhe o
valor verdadeiro, que dava para pagar dois anos de universidade.
A historia correu o bairro, como correm sempre estas coisas, de balcao em
balcao, e as pessoas comecaram a voltar a livraria, primeiro por curiosidade,
depois por costume. Traziam livros velhos para avaliar, ficavam a conversar,
compravam um ou outro romance. A rapariga, que estudava letras, passou a
aparecer aos sabados para ajudar a organizar as estantes, e Joaquim ensinou
lhe a reconhecer o papel antigo pelo cheiro e a encadernacao boa pelo peso na
mao.
No inverno o rio subiu e alagou as caves da rua toda. Os vizinhos
apareceram sem que ninguem chamasse, o alfaiate, a dona da casa de cha, os
estudantes da pensao, e durante uma noite inteira passaram livros de mao em
mao para o primeiro andar, como quem salva criancas de um incendio. Perdeu
se pouco, no fim de contas, e o que se perdeu Joaquim disse que ja estava
lido. No dia seguinte a casa de cha ofereceu bolos a toda a gente e a rua
inteira almocou na livraria, entre caixas molhadas e risos.
Quando Joaquim fez oitenta anos, juntou os amigos e anunciou que estava na
hora de descansar. Houve um silencio triste, porque toda a gente percebeu
que a livraria ia fechar, e aquela rua sem a livraria seria outra rua. Mas
ele tirou do bolso uma chave presa numa fita azul e estendeu a a rapariga,
que ja nao era rapariga, era uma mulher formada que dava aulas na escola do
bairro. Disse apenas que os livros conhecem os seus donos, e que aqueles ja
a tinham escolhido havia muito tempo.
Ela mudou pouca coisa, pintou a porta, pos uma mesa com cadeiras ao fundo
para quem quisesse ler sem pressa, e pendurou atras do balcao o retrato do
velho livreiro a ler, tirado numa manha de sol sem ele dar conta. Joaquim
ainda aparece quase todos os dias, senta se na cadeira do fundo, aceita um
cha e finge que esta apenas de passagem. Os clientes novos pensam que ele e
um avo da dona, e nem ele nem ela acham necessario corrigir ninguem.
"""

CONTROL_EN = """
The expedition reached the high valley on the ninth day, later than planned
and short of supplies. Snow had closed the southern pass behind them, and
the mules were tired and thin. Doctor Hale ordered camp to be made beside
the frozen stream while there was still light, and sent the two strongest
porters ahead to look for the stone marker described in the journals of the
first survey. If the marker existed, the route to the glacier would be
clear. If it did not, they would have to turn back and admit that two years
of preparation had ended in nothing.
The porters returned after dark with news that changed everything. They had
found not one marker but three, set in a line pointing north, each cut with
the same spiral sign. Hale sat by the fire turning his cup in his hands and
said little. The journals mentioned a single stone. Three stones in a line
meant that someone had come here after the first survey, someone with reasons
of their own, and the spiral sign belonged to no expedition he had ever read
about. In the morning they followed the line of markers up the valley. The
walking was hard, over loose rock glazed with ice, and the wind came down
the glacier in long cold pulls that made the ropes sing. At noon the
youngest of the party, a student named Ferris, spotted a fourth stone half
buried in the moraine, and beneath it, wrapped in oiled cloth, a tin box
containing a notebook. The pages were brittle but readable. The hand was
small and steady, and the first entry was dated forty years earlier, almost
to the day. The writer gave no name. He described climbing alone into the
valley in late autumn, against all advice, to test a theory he did not fully
explain. There was a chamber under the ice, he wrote, where the glacier met
the rock wall, and inside it the air moved as if the mountain itself were
breathing. He had measured the warm current for six days. The last entries
were hurried. The weather had turned, his fuel was nearly gone, and he meant
to leave the notebook under a marked stone so that whoever came after him
would not waste years proving what he already knew. The final line said
simply that the mountain keeps its accounts and pays its debts, and that he
was going down while his legs still obeyed him. Nobody in the party spoke
for a while after Hale finished reading aloud. Then Ferris asked the
question all of them were holding, whether the man had ever come down. Hale
closed the notebook and looked up the valley to where the ice wall stood
blue and quiet in the afternoon light. There was no record of him, he said,
in any archive he knew, and archives were his trade. Whoever he was, he had
walked out of the world here, and the stones were either his road home or
his grave marks. They found the chamber on the third day of searching,
exactly where the notebook placed it, behind a curtain of ice that had
thinned with the warm years. The air inside did move, slow and steady, warmer
than the glacier had any right to be, rising from a crack that ran down into
darkness past the reach of their lamps. Hale took his measurements with
shaking hands. The current was real, the temperatures matched the old
figures, and every page of the nameless notebook held up. Science had a new
question, the kind that builds careers and fills journals for a generation.
But it was Ferris who found the second tin box, set in a niche above the
crack, and in it nothing but a compass with its needle bent to point forever
downward, and a single sheet of paper with one line in the same small hand.
It said, if you have come this far, leave something of your own, for the
account is never closed. They argued about it that night, science against
superstition, and science won as it usually does in tents at altitude. Yet
in the morning, before the descent, each of them went alone into the chamber
for a moment, and none of them ever said what he left there, and the
expedition came down the mountain complete and healthy into the first warm
week of spring.
"""

CONTROL_DE = """
Das Archiv der kleinen Universitaet lag im Keller des Nordfluegels, drei
Treppen unter der Bibliothek, hinter einer Tuer, die niemand mehr benutzte.
Als die junge Archivarin Lena Hartmann ihre Stelle antrat, gab ihr der alte
Verwalter einen Ring mit elf Schluesseln und sagte, der zwoelfte sei seit dem
Krieg verloren, und die Tuer, zu der er gehoere, solle sie einfach vergessen,
so wie alle vor ihr es getan haetten. Natuerlich konnte sie es nicht
vergessen. Wer einen Beruf waehlt, der aus dem Ordnen alter Papiere besteht,
der waehlt ihn, weil verschlossene Tueren ihm keine Ruhe lassen. Sie fand
die Tuer am Ende des laengsten Ganges, niedrig und aus schwerem Holz, mit
einem Schloss, das aelter war als das Gebaeude selbst. Monatelang ging sie
daran vorbei, jeden Tag, und jeden Tag blieb sie ein wenig laenger davor
stehen. Im Februar, waehrend draussen der Schnee die Stadt leise machte,
begann sie in den Bestandsbuechern zu suchen. Drei Woechen brauchte sie, um
die erste Spur zu finden, einen Eintrag von achtzehnhundertzwoelf ueber die
Verwahrung der Sammlung eines Professors der Sternkunde, dessen Name spaeter
sorgfaeltig durchgestrichen worden war. Die Sammlung umfasste laut Eintrag
vierzig Kisten, ein Fernrohr und ein Verzeichnis der Beobachtungen aus
dreissig Jahren. Kein anderes Buch erwaehnte sie je wieder. Es war, als
haette die Universitaet beschlossen, einen ihrer eigenen Gelehrten
rueckwaerts aus der Geschichte zu schreiben. Der Schluessel fand sich
schliesslich dort, wo wichtige Dinge sich immer finden, am falschen Ort. Er
lag in einer Blechdose mit der Aufschrift Ersatzteile, zwischen Schrauben
und alten Siegelresten, und er passte beim ersten Versuch. Hinter der Tuer
war kein Raum, sondern eine Treppe, und unter der Treppe ein Gewoelbe, das
trockener und waermer war, als es ein Keller sein durfte. Die vierzig
Kisten standen an der Wand, ordentlich gestapelt, als seien sie gestern
gebracht worden. Auf dem Tisch in der Mitte aber lag, aufgeschlagen und mit
einem Lineal beschwert, das Verzeichnis der Beobachtungen, und daneben stand
ein Becher, in dem vor sehr langer Zeit einmal Tee gewesen war. Lena las
die aufgeschlagene Seite im Licht ihrer Lampe. Der Professor hatte in seiner
letzten Nacht einen Stern verzeichnet, der in keinem Katalog stand, hell und
rot und genau ueber dem Turm der Universitaet, und er hatte daruntergesetzt,
dass er am Morgen dem Rektor berichten werde, was er gesehen habe, denn der
Himmel gehoere allen und nicht den Vorsichtigen. Ein juengerer Eintrag von
fremder Hand stand darunter, nur ein Satz, der Professor sei beurlaubt und
die Sammlung versiegelt, zum Schutze der Ruhe der Anstalt. Sie verbrachte
den Fruehling damit, die Kisten zu oeffnen und zu verzeichnen, abends und an
den Wochenenden, ohne jemandem davon zu erzaehlen. Die Beobachtungen waren
praezise, die Instrumente meisterhaft, und der rote Stern fand sich in den
Aufzeichnungen von vier weiteren Naechten, immer kurz vor der Daemmerung,
immer ueber dem Turm. Im Juni schrieb sie an die Sternwarte der Hauptstadt
und bat um Pruefung, und im August kam die Antwort, hoeflich und erstaunt,
man habe die Position berechnet und dort stehe tatsaechlich etwas, ein
veraenderlicher Stern, der alle siebzig Jahre fuer wenige Naechte aufleuchte,
und der naechste Termin falle in den kommenden Oktober. In der ersten
Oktobernacht stieg die ganze Fakultaet auf den Turm, mit Thermoskannen und
Decken und dem alten Fernrohr des Professors, das die Werkstatt liebevoll
gereinigt hatte. Kurz vor der Daemmerung kam der Stern, hell und rot und
puenktlich wie eine beglichene Schuld, und die Universitaet, die einen Namen
einst durchgestrichen hatte, schrieb ihn in derselben Woche gross ueber die
Tuer ihres neuen Hoersaals.
"""
