# This is the title of and MD file click on the nav for the notebooks

<p class="subtitle">
TL'DR This is the subtitle of the post
</p>

Text can be **bold**, _italic_, or ~~strikethrough~~. [Links](https://github.com) should be blue with no underlines (unless hovered over).

There should be whitespace between paragraphs. There should be whitespace between paragraphs. There should be whitespace between paragraphs. There should be whitespace between paragraphs.

There should be whitespace between paragraphs. There should be whitespace between paragraphs. There should be whitespace between paragraphs. There should be whitespace between paragraphs.

> There should be no margin above this first sentence.
>
> Blockquotes should be a lighter gray with a gray border along the left side.
>
> There should be no margin below this final sentence.

# Header 1

This is a normal paragraph following a header. Bacon ipsum dolor sit amet t-bone doner shank drumstick, pork belly porchetta chuck sausage brisket ham hock rump pig. Chuck kielbasa leberkas, pork bresaola ham hock filet mignon cow shoulder short ribs biltong.

## Header 2

> This is a blockquote following a header. Bacon ipsum dolor sit amet t-bone doner shank drumstick, pork belly porchetta chuck sausage brisket ham hock rump pig. Chuck kielbasa leberkas, pork bresaola ham hock filet mignon cow shoulder short ribs biltong.

### Header 3

```
This is a code block following a header.
```

#### Header 4

* This is an unordered list following a header.
* This is an unordered list following a header.
* This is an unordered list following a header.

##### Header 5

1. This is an ordered list following a header.
2. This is an ordered list following a header.
3. This is an ordered list following a header.

###### Header 6

| What      | Follows         |
|-----------|-----------------|
| A table   | A header        |
| A table   | A header        |
| A table   | A header        |

----------------

There's a horizontal rule above and below this.

----------------

Here is an unordered list:

* Salt-n-Pepa
* Bel Biv DeVoe
* Kid 'N Play

And an ordered list:

1. Michael Jackson
2. Michael Bolton
3. Michael Bublé

And an unordered task list:

- [x] Create a sample markdown document
- [x] Add task lists to it
- [ ] Take a vacation

And a "mixed" task list:

- [ ] Steal underpants
- ?
- [ ] Profit!

And a nested list:

* Jackson 5
  * Michael
  * Tito
  * Jackie
  * Marlon
  * Jermaine
* TMNT
  * Leonardo
  * Michelangelo
  * Donatello
  * Raphael

Definition lists can be used with HTML syntax. Definition terms are bold and italic.

<dl>
    <dt>Name</dt>
    <dd>Godzilla</dd>
    <dt>Born</dt>
    <dd>1952</dd>
    <dt>Birthplace</dt>
    <dd>Japan</dd>
    <dt>Color</dt>
    <dd>Green</dd>
</dl>

----------------

Tables should have bold headings and alternating shaded rows.

| Artist            | Album           | Year |
|-------------------|-----------------|------|
| Michael Jackson   | Thriller        | 1982 |
| Prince            | Purple Rain     | 1984 |
| Beastie Boys      | License to Ill  | 1986 |

If a table is too wide, it should condense down and/or scroll horizontally.

| Artist            | Album           | Year | Label       | Awards   | Songs     |
|-------------------|-----------------|------|-------------|----------|-----------|
| Michael Jackson   | Thriller        | 1982 | Epic Records | Grammy Award for Album of the Year, American Music Award for Favorite Pop/Rock Album, American Music Award for Favorite Soul/R&B Album, Brit Award for Best Selling Album, Grammy Award for Best Engineered Album, Non-Classical | Wanna Be Startin' Somethin', Baby Be Mine, The Girl Is Mine, Thriller, Beat It, Billie Jean, Human Nature, P.Y.T. (Pretty Young Thing), The Lady in My Life |
| Prince            | Purple Rain     | 1984 | Warner Brothers Records | Grammy Award for Best Score Soundtrack for Visual Media, American Music Award for Favorite Pop/Rock Album, American Music Award for Favorite Soul/R&B Album, Brit Award for Best Soundtrack/Cast Recording, Grammy Award for Best Rock Performance by a Duo or Group with Vocal | Let's Go Crazy, Take Me With U, The Beautiful Ones, Computer Blue, Darling Nikki, When Doves Cry, I Would Die 4 U, Baby I'm a Star, Purple Rain |
| Beastie Boys      | License to Ill  | 1986 | Mercury Records | noawardsbutthistablecelliswide | Rhymin & Stealin, The New Style, She's Crafty, Posse in Effect, Slow Ride, Girls, (You Gotta) Fight for Your Right, No Sleep Till Brooklyn, Paul Revere, Hold It Now, Hit It, Brass Monkey, Slow and Low, Time to Get Ill |

----------------

Code snippets like `var foo = "bar";` can be shown inline.

Also, `this should vertically align` ~~`with this`~~ ~~and this~~.

Code can also be shown in a block element.
```
var foo = "bar";
```

Code can also use syntax highlighting.
```javascript
var foo = "bar";
```

```
Long, single-line code blocks should not wrap. They should horizontally scroll if they are too long. This line should be long enough to demonstrate this.
```

```javascript
var foo = "The same thing is true for code with syntax highlighting. A single line of code should horizontally scroll if it is really long.";
```

Inline code inside table cells should still be distinguishable.

| Language    | Code               |
|-------------|--------------------|
| Javascript  | `var foo = "bar";` |
| Ruby        | `foo = "bar"`      |

----------------

Small images should be shown at their actual size.

![](http://placekitten.com/g/300/200/)

Large images should always scale down and fit in the content container.

![](http://placekitten.com/g/1200/800/)

```
This is the final element on the page and there should be no margin below this.
```

# Custom things

Some Python code:

<div class="pre-filename">File: my_script.py</div>

```python
id_ = 0
for directory in directories:
    rootdir = os.path.join('/Users/drodriguez/Downloads/aclImdb', directory)
    for subdir, dirs, files in os.walk(rootdir):
        for file_ in files:
            with open(os.path.join(subdir, file_), 'r') as f:
                doc_id = '_*%i' % id_
                id_ = id_ + 1

                text = f.read()
                text = text.decode('utf-8')
                tokens = nltk.word_tokenize(text)
                doc = ' '.join(tokens).lower()
                doc = doc.encode('ascii', 'ignore')
                input_file.write('%s %s\n' % (doc_id, doc))
```

Our terminal design:

```terminal
$ echo "hello world!"
hello work

$ cat file.pem
{}

$ A test of the dollar sign in a line  $$$$
$ This ones above should be selectable ^^^^
```

This is a `figure`!!

{{< figure src="http://placekitten.com/g/300/200/" title="Kitten" >}}

The different type of notes we have:

<p class="note">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur purus mi, sollicitudin ac justo a, dapibus ultrices dolor. Curabitur id eros mattis, tincidunt ligula at, condimentum urna. Morbi accumsan, risus eget porta consequat, tortor nibh blandit dui, in sodales quam elit non erat. Aenean lorem dui, lacinia a metus eu, accumsan dictum urna. Sed a egestas mauris, non porta nisi. Suspendisse eu lacinia neque. Morbi gravida eros non augue pharetra, condimentum auctor purus porttitor.</p>

<p class="update">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur purus mi, sollicitudin ac justo a, dapibus ultrices dolor. Curabitur id eros mattis, tincidunt ligula at, condimentum urna. Morbi accumsan, risus eget porta consequat, tortor nibh blandit dui, in sodales quam elit non erat. Aenean lorem dui, lacinia a metus eu, accumsan dictum urna. Sed a egestas mauris, non porta nisi. Suspendisse eu lacinia neque. Morbi gravida eros non augue pharetra, condimentum auctor purus porttitor.</p>

<p class="alert">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur purus mi, sollicitudin ac justo a, dapibus ultrices dolor. Curabitur id eros mattis, tincidunt ligula at, condimentum urna. Morbi accumsan, risus eget porta consequat, tortor nibh blandit dui, in sodales quam elit non erat. Aenean lorem dui, lacinia a metus eu, accumsan dictum urna. Sed a egestas mauris, non porta nisi. Suspendisse eu lacinia neque. Morbi gravida eros non augue pharetra, condimentum auctor purus porttitor.</p>
