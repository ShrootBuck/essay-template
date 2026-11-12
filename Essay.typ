#let title = "Essay Title"
#let author = "Zayd Krunz"
#let school = "BASIS Tucson North"
#let course = "[Course Name]"
#let date = datetime.today().display("[month repr:long] [day padding:none], [year]")

#set document(title: title, author: author)
#set page(paper: "us-letter", margin: 1in)
#set text(font: ("Times New Roman", "Libertinus Serif"), size: 12pt)
#let words = counter("essay-words")

#align(center)[
  #v(1.5cm)
  #text(size: 21pt, weight: "bold", title)

  #v(1.5cm)
  #author \
  #school

  #v(1fr)
  *Word Count: #context words.final().first()*

  #v(1fr)
  #course \
  #date
]

#set page(numbering: "1")
#counter(page).update(1)
#set par(leading: 15pt, spacing: 15pt, justify: true)
#block(width: 100%)[
  #set par(first-line-indent: (amount: 0.5in, all: true))
  #show regex("[\\p{L}\\p{N}]+(?:[’'‐-][\\p{L}\\p{N}]+)*"): word => {
    words.step()
    word
  }

  = Subheading

  Paragraphs begin here.
]

#pagebreak()
#align(center)[*References*]
#set par(hanging-indent: 0.5in)

References go here.
