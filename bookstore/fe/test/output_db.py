from fe.access import book

book_db = book.BookDB()
books = book_db.get_book_info(0, 0)

with open('output.txt', 'w') as f:
    for b in books:
        b_dict = b.__dict__.copy()
        b_dict.pop('pictures', None)
        b_dict.pop('author_intro', None)
        b_dict.pop('book_intro', None)
        # b_dict.pop('content', None)
        
        for k, v in b_dict.items():
            f.write(f'{k}: {v}\n')
        f.write('\n\n')