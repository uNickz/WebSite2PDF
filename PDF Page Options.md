# List of all [PDF Page Options](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-printToPDF)

> - ```landscape```
>     - **Type**: __bool, optional__
>     - **Description**: __Paper orientation. Defaults to false.__
> 
> - ```displayHeaderFooter```
>     - **Type**: __bool, optional__
>     - **Description**: __Display header and footer. Defaults to false.__
>     
> - ```printBackground```
>     - **Type**: __bool, optional__
>     - **Description**: __Print background graphics. Defaults to false.__
>     
> - ```scale```
>     - **Type**: __float, optional__
>     - **Description**: __Scale of the webpage rendering. Defaults to 1.__
>     
> - ```paperWidth```
>     - **Type**: __float, optional__
>     - **Description**: __Paper width in inches. Defaults to 8.5 inches.__
>     
> - ```paperHeight```
>     - **Type**: __float, optional__
>     - **Description**: __Paper height in inches. Defaults to 11 inches.__
>     
> - ```marginTop```
>     - **Type**: __float, optional__
>     - **Description**: __Top margin in inches. Defaults to 1cm (~0.4 inches).__
>     
> - ```marginBottom```
>     - **Type**: __float, optional__
>     - **Description**: __Bottom margin in inches. Defaults to 1cm (~0.4 inches).__
>     
> - ```marginLeft```
>     - **Type**: __float, optional__
>     - **Description**: __Left margin in inches. Defaults to 1cm (~0.4 inches).__
>     
> - ```marginRight```
>     - **Type**: __float, optional__
>     - **Description**: __Right margin in inches. Defaults to 1cm (~0.4 inches).__
>     
> - ```pageRanges```
>     - **Type**: __str, optional__
>     - **Description**: __Paper ranges to print, one based, e.g., "1-5, 8, 11-13". Pages are printed in the document order, not in the order specified, and no more than once. Defaults to empty string, which implies the entire document is printed. The page numbers are quietly capped to actual page count of the document, and ranges beyond the end of the document are ignored. If this results in no pages to print, an error is reported. It is an error to specify a range with start greater than end.__
>     
> - ```headerTemplate```
>     - **Type**: __str, optional__
>     - **Description**: __HTML template for the print header. Should be valid HTML markup with following classes used to inject printing values into them:__
>         - ``date``: __formatted print date.__
>         - ``title``: __document title.__
>         - ``url``: __document location.__
>         - ``pageNumber``: __current page number.__
>         - ``totalPages``: __total pages in the document.__
>     - __For example,__ ``<span class=title></span>`` __would generate span containing the title.__
>     
> - ```footerTemplate```
>     - **Type**: __str, optional__
>     - **Description**: __HTML template for the print footer. Should use the same format as the__ ``headerTemplate``__.__
>     
> - ```preferCSSPageSize```
>     - **Type**: __bool, optional__
>     - **Description**: __Whether or not to prefer page size as defined by css. Defaults to false, in which case the content will be scaled to fit the paper size.__
>     
> - ```transferMode``` **[*EXPERIMENTAL* => This may be changed, moved or removed]**
>     - **Type**: __str, optional__
>     - **Description**: __Return as stream. Allowed Values:__ ``ReturnAsBase64``__,__ ``ReturnAsStream``__. Defaults to ReturnAsBase64.__
>     - **Pay Attention**: __At the moment the ``ReturnAsStream`` option doesn't work.__