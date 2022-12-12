#lang racket

(require redex)

(define-language VPC
  (v ::= variable-not-otherwise-mentioned)   ;; expression variables
  (d ::= variable-not-otherwise-mentioned)   ;; dimension variables
  (D ::= number)                             ;; dimension names
  (δ ::= d D)                                ;; dimensions
  (ϕ ::= v d)                                ;; variables
  (s ::= l r)                                ;; selectors
  (* ::= @ λ)                                ;; abstraction annotations
  (e ::= κ (* (ϕ) e) (e e) v                 ;; lambda calculus + constants
     (let v = e in e)                        ;; recursive let
     δ                                       ;; dimensions
     (δ e e)                                 ;; choice
     (δ s -> e)                              ;; selection
     (any d from e in e else e)              ;; any dimension pick
     (the δ from e in e else e)              ;; specific dimension pick
     (e + e))             
  (ebar ::= κ D (* (ϕ) e) (D ebar ebar))     ;; values
  (σ ::= (split e on e e)                    ;; split on
     (split e on e e else e)                 ;; split on else
     (split e on any e e else e))            ;; split on any else
  (C ::= hole (C e) (e C)                    ;; contexts
     (δ C e) (δ e C)
     (let v = C in e) (let v = e in C)
     (any d from C in e else e)
     (the δ from C in e else e)
     (any d from e in C else e)
     (the δ from e in C else e)
     (any d from e in e else C)
     (the δ from e in e else C))
  #:binding-forms
  (* (ϕ) e #:refers-to ϕ)
  (any d from e in e #:refers-to d else e))

(default-language VPC)

(define (minimum lst curr)
  (cond
    ((null? lst) curr)
    ((< (car lst) curr)
     (minimum (cdr lst) (car lst)))
    (else
     (minimum (cdr lst) curr))))

(define (mymin lst)
  (if (null? lst)
      #f
      (minimum (cdr lst) (car lst))))

(define-metafunction VPC
  dims : e -> (δ ...)
  [(dims κ) ()]
  [(dims D) ,(list (term D))]
  [(dims d) ()]
  [(dims (* (v) e)) (dims e)]
  [(dims (* (d) e)) ,(remove (term d) (term (dims e)))]
  [(dims (e_1 e_2)) ,(append (term (dims e_1)) (term (dims e_2)))]
  [(dims (δ e_1 e_2)) ,(append (list (term δ)) (term (dims e_1)) (term (dims e_2)))]
  [(dims (δ s -> e)) ,(remove (term δ) (term (dims e)))]
  [(dims (any d from e in e_1 else e_2)) ,(if (not (eq? '() (term (dims e))))
                                              (remove (term d) (term (dims e_1)))
                                              (term (dims e_2)))]
  [(dims (the δ from e in e_1 else e_2)) ,(if (not (eq? (member (term δ) (term (dims e))) #f))
                                              (term (dims e_1))
                                              (term (dims e_2)))])


(define-metafunction VPC
  split_eval : σ -> e
  [(split_eval (split e_1 on (δ v_1 v_2) e_2)) ((λ (v_1) ((λ (v_2) e_2) (δ r -> e_1))) (δ l -> e_1))]
  [(split_eval (split e_1 on (δ v_1 v_2) e_2 else e_3)) (the δ from e_1 in (split e_1 on (δ v_1 v_2) e_2) else e_3)]
  [(split_eval (split e_1 on any (δ v_1 v_2) e_2 else e_3)) (any δ from e_1 in e_2 else e_3)])


(define ->VPC
  (reduction-relation
   VPC
   
   [--> (D l (D ebar_1 ebar_2))
        (D l -> ebar_1)
        Chc-Elim-L]

   [--> (D r (D ebar_1 ebar_2))
        (D r -> ebar_2)
        Chc-Elim-R]
   
   [--> (δ s -> κ)
        κ
        Sel-Idemp-K]

   [--> (δ s -> D)
        D
        Sel-Idemp-D]

   [--> ((λ (ϕ) e) (δ e_1 e_2))
        (δ ((λ (ϕ) e) e_1) ((λ (ϕ) e) e_2))
        App-Reduce-If]

   [--> ((λ (ϕ) e_1) e_2)
        (substitute e_1 ϕ e_2)
        (side-condition (not (redex-match? VPC (δ e_1 e_2) (term e_2))))
        App-Reduce-Else]

   [--> ((@ (ϕ) e) e_1)
        (substitute e ϕ e_1)
        App@-Reduce]

   [--> (any d from ebar in e else e_1)
        (substitute e d ,(mymin (term (dims ebar))))
        (side-condition (not (eq? (term (dims ebar)) '())))
        Any-Reduce-Then]

   [--> (any d from ebar in e else e_1)
        e_1
        Any-Reduce-Else]

   [--> (the δ from ebar in e else e_1)
        e
        (side-condition (member (term δ) (term (dims ebar))))
        The-Reduce-Then]

   [--> (the δ from ebar in e else e_1)
        e_1
        The-Reduce-Else]

   [--> (δ s -> (let v = e in e_1))
        (let v = (δ s -> e) in (δ s -> e_1))
        Sel-Let]

   [--> ((δ e_1 e_2) e_3)
        (δ (e_1 (δ l -> e_3)) (e_2 (δ r -> e_3)))
        App-Chc]

   [--> (δ s -> (e_1 e_2))
        ((δ s -> e_1) (δ s -> e_2))
        Sel-App]
   
   [--> (δ s -> (* (v) e))
        (* (v) (δ s -> e))
        Sel-Abs-Exp]

   [--> (δ s -> (* (d_1) e))
        (* (d_1) (δ s -> e))
        Sel-Abs-Dim]

   [--> (δ s -> (any d from e in e_1 else e_2))
        (any d from (δ s -> e) in
             (δ s -> e_1)
             else (δ s -> e_2))
        Sel-Any]
   
   [--> (δ s -> (the δ_1 from e in e_1 else e_2))
        (the δ_1 from (δ s -> e) in (δ s -> e_1) else (δ s -> e_2))
        Sel-The]

   [--> (D_1 s -> (D_2 e_1 e_2))
        (D_2 (D_1 s -> e_1) (D_1 s -> e_2))
        (side-condition
         (not
          (eq?
           (term D_1)
           (term D_2))))
        Sel-Chc]))

(define -->VPC
  (compatible-closure ->VPC VPC C))

(define-metafunction VPC
  add : e e -> e
  [(add (δ e_1 e_2) (δ e_3 e_4)) (δ (add e_1 e_3) (add e_2 e_4))]
  [(add e_1 (δ e_2 e_3)) (add (δ e_1 e_1) (δ e_2 e_3))]
  [(add e_1 e_2) (e_1 + e_2)])
  

(traces -->VPC (term ((λ (ϕ) (add ϕ κ_1)) (1 κ_2 κ_3))))

;(traces -->VPC (term ((λ (ϕ) (add ϕ (1 κ_1 κ_2))) (2 κ_3 κ_4))))

;(traces -->VPC (term ((@ (x) (a 5 x)) (4 1 2))))

;(traces -->VPC (term ((λ (x) (a 5 x)) (4 1 2))))

;(traces -->VPC (term (split_eval (split (4 1 2) on any (d v_1 v_2) (4 ((λ (x) (a 5 x)) 1) ((λ (x) (a 5 x)) 2)) else (substitute (a 5 x) x (4 1 2))))))

(test-equal (term (dims κ)) (term ()))
(test-equal (term (dims 1)) (term (1)))
(test-equal (term (dims a)) (term ()))
(test-equal (term (dims (@ (x) 1))) (term (1)))
(test-equal (term (dims (1 2))) (term (1 2)))
(test-equal (term (dims ((2 3) 4))) (term (2 3 4)))
(test-equal (term (dims (λ (a) (a 1)))) (term (1)))
(test-equal (term (dims (1 2 3))) (term (1 2 3)))
(test-equal (term (dims (1 (2 3) (4 5)))) (term (1 2 3 4 5)))
(test-equal (term (dims (3 l -> 3))) (term ()))
(test-equal (term (dims (any a from 2 in 3 else 4))) (term (3)))
(test-equal (term (dims (any a from 2 in (a 3) else 4))) (term (3)))
(test-equal (term (dims (any a from κ in 3 else 4))) (term (4)))
(test-equal (term (dims (the 1 from (1 2) in 3 else 4))) (term (3)))
(test-equal (term (dims (the 1 from (2 3) in 4 else 5))) (term (5)))

;; Chc-Elim-L
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (1 l (1 4 5))))))
 (term 4))

;; Sel-Idemp-K
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (1 l -> κ)))))
 (term κ))

;; Sel-Idemp-D
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (1 l -> 2)))))
 (term 2))

;; App@-Reduce
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term ((@ (x) (x z)) y)))))
 (term (y z)))

;; App-Reduce-Then
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (any a from (1 2 3) in (a 4 5) else 3)))))
 (term (1 4 5)))

;; App-Reduce-Else
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (any a from κ in (a 4 5) else 3)))))
 (term 3))

;; The-Reduce-Then
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (the 1 from (1 2 3) in 4 else 5)))))
 (term 4))

;; The-Reduce-Else
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (the 1 from κ in 4 else 5)))))
 (term 5))

;; Sel-Let
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (a l -> (let x = 1 in 2))))))
 (term (let x = 1 in 2)))

;; App-Chc
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term ((a 1 2) 3)))))
 (term (a (1 3) (2 3))))

;; Sel-App
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (a l -> (1 2))))))
 (term (1 2)))

;; Tests Sel-App
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (1 r -> (x y))))))
 (term ((1 r -> x) (1 r -> y))))

;; Tests Sel-Abs-Dim
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (1 r -> (@ (a) x))))))
 (term (@ (a) (1 r -> x))))

;; Tests Sel-Abs-Exp
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (4 r -> (λ (x) z))))))
 (term (λ (x) (4 r -> z))))

;; Tests App-Chc
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term ((4 x y) z)))))
 (term (4 (x (4 l -> z)) (y (4 r -> z)))))

;;Tests Sel-Let
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (4 r -> (let x = y in z))))))
 (term (let x = (4 r -> y) in (4 r -> z))))

;;Tests Sel-Abs-Exp
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (1 r -> (λ (a) 3))))))
 (term (λ (a) (1 r -> 3))))

;;Tests Sel-The
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (4 r -> (the 3 from x in y else z))))))
 (term (the 3 from (4 r -> x) in (4 r -> y) else (4 r -> z))))

;;Tests Sel-Any
(test-equal
 (term
  ,(first
    (apply-reduction-relation*
     -->VPC
     (term (4 r -> (any a from x in y else z))))))
 (term (any a from (4 r -> x) in (4 r -> y) else (4 r -> z))))