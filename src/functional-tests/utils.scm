(library
  (utils)
  (export inc! dec!

          swap!
          slurp-file
          chomp
          hotpatch-sym
          indirect-lambda
          set-lambda!
          dlambda

          all? some? none?)

  (import (chezscheme)
          (only (srfi s1 lists) drop-while))

  (define-syntax inc!
    (syntax-rules ()
      ((_ v) (set! v (+ 1 v)))
      ((_ v n) (set! v (+ n v)))))

  (define-syntax dec!
    (syntax-rules ()
      ((_ v) (set! v (- v 1)))
      ((_ v n) (set! v (- v n)))))

  (define-syntax swap!
    (syntax-rules ()
      ((_ x y)
       (let ((tmp x))
        (set! x y)
        (set! y tmp)))))

  (define (slurp-file path)
    (define (slurp)
      (let ((output (get-string-all (current-input-port))))
       (if (eof-object? output)
           output
           (chomp output))))

    (with-input-from-file path slurp))

  (define (chomp line)
    (list->string
      (reverse
        (drop-while char-whitespace?
                    (reverse (string->list line))))))

  (define hotpatch-sym (gensym))

  (define-syntax indirect-lambda
    (syntax-rules ()
      ((_ params b1 b2 ...)
      (let ((this (lambda params b1 b2 ...)))
        (lambda args
          (if (and (= (length args) 2)
                   (eq? (car args) hotpatch-sym))
              (set! this (cadr args))
              (apply this args)))))))

  (define (set-lambda! fn new-fn)
    (fn hotpatch-sym new-fn))

  (define-syntax dlambda
    (syntax-rules ()
      ((_ (name params b1 b2 ...) ...)
       (lambda (m . args)
               (apply (case m
                            [(name) (lambda params b1 b2 ...)] ...)
                      args)))))

  ;; FIXME: why aren't these in core scheme? what do people use instead?
  (define (all? pred xs)
    (let loop ((xs xs))
     (if (null? xs)
         #t
         (if (pred (car xs))
             (loop (cdr xs))
             #f))))

  (define (some? pred xs)
    (let loop ((xs xs))
     (if (null? xs)
         #f
         (if (pred (car xs))
             #t
             (loop (cdr xs))))))

  (define (none? pred xs)
    (not (all? pred xs)))
  )
